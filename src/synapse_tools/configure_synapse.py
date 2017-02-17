"""Update the synapse configuration file and restart synapse if anything has
changed."""

import copy
import filecmp
import json
import os
import shutil
import subprocess
import tempfile

import yaml
from environment_tools.type_utils import available_location_types
from environment_tools.type_utils import compare_types
from environment_tools.type_utils import get_current_location
from paasta_tools.marathon_tools import get_all_namespaces
from yaml import CLoader


def get_config(synapse_tools_config_path):
    with open(synapse_tools_config_path) as synapse_config:
        return set_defaults(json.load(synapse_config))


def set_defaults(config):
    config.setdefault('haproxy.defaults.inter', '10m')
    config.setdefault('file_output_path', '/var/run/synapse/services')
    config.setdefault('haproxy_socket_file_path', '/var/run/synapse/haproxy.sock')
    config.setdefault('haproxy_config_path', '/var/run/synapse/haproxy.cfg')
    config.setdefault('maximum_connections', 10000)
    config.setdefault('maxconn_per_server', 50)
    config.setdefault('maxqueue_per_server', 10)
    config.setdefault('haproxy_socket_file_path', '/var/run/synapse/haproxy.sock')
    config.setdefault('synapse_restart_command', ['service', 'synapse', 'restart'])
    config.setdefault('zookeeper_topology_path', '/nail/etc/zookeeper_discovery/infrastructure/local.yaml')
    config.setdefault('haproxy_path', '/usr/bin/haproxy-synapse')
    config.setdefault('haproxy_config_path', '/var/run/synapse/haproxy.cfg')
    config.setdefault('haproxy_pid_file_path', '/var/run/synapse/haproxy.pid')
    config.setdefault('reload_cmd_fmt', """sudo /usr/bin/synapse_qdisc_tool protect bash -c 'touch {haproxy_pid_file_path} && PID=$(cat {haproxy_pid_file_path}) && {haproxy_path} -f {haproxy_config_path} -p {haproxy_pid_file_path} -sf $PID && sleep 0.010'""")
    config.setdefault('hacheck_port', 6666)
    config.setdefault('stats_port', 3212)
    return config


def get_zookeeper_topology(zookeeper_topology_path):
    with open(zookeeper_topology_path) as fp:
        zookeeper_topology = yaml.load(fp, Loader=CLoader)
    zookeeper_topology = [
        '%s:%d' % (entry[0], entry[1]) for entry in zookeeper_topology]
    return zookeeper_topology


def generate_base_config(synapse_tools_config):
    synapse_tools_config = synapse_tools_config
    haproxy_inter = synapse_tools_config['haproxy.defaults.inter']
    base_config = {
        # We'll fill this section in
        'services': {},
        'file_output': {'output_directory': synapse_tools_config['file_output_path']},
        'haproxy': {
            'bind_address': synapse_tools_config['bind_addr'],
            'restart_interval': 60,
            'restart_jitter': 0.1,
            'state_file_path': '/var/run/synapse/state.json',
            'state_file_ttl': 30 * 60,
            'reload_command': synapse_tools_config['reload_cmd_fmt'].format(**synapse_tools_config),
            'socket_file_path': synapse_tools_config['haproxy_socket_file_path'],
            'config_file_path': synapse_tools_config['haproxy_config_path'],
            'do_writes': True,
            'do_reloads': True,
            'do_socket': True,

            'global': [
                'daemon',
                'maxconn %d' % synapse_tools_config['maximum_connections'],
                'stats socket %s level admin' % synapse_tools_config['haproxy_socket_file_path'],

                # Default of 16k is too small and causes HTTP 400 errors
                'tune.bufsize 32768',

                # Add random jitter to checks
                'spread-checks 50',

                # Send syslog output to syslog2scribe
                'log 127.0.0.1:1514 daemon info',
                'log-send-hostname',
                'unix-bind mode 666'

            ],

            'defaults': [
                # Various timeout values
                'timeout connect 200ms',
                'timeout client 1000ms',
                'timeout server 1000ms',

                # On failure, try a different server
                'retries 1',
                'option redispatch',

                # The server with the lowest number of connections receives the
                # connection
                'balance leastconn',

                # Assume it's an HTTP service
                'mode http',

                # Actively close connections to prevent old HAProxy instances
                # from hanging around after restarts
                'option forceclose',

                # Sometimes our headers contain invalid characters which would
                # otherwise cause HTTP 400 errors
                'option accept-invalid-http-request',

                # Use the global logging defaults
                'log global',

                # Log any abnormal connections at 'error' severity
                'option log-separate-errors',

                # Normally just check at <inter> period in order to minimize load
                # on individual services.  However, if we get anything other than
                # a 100 -- 499, 501 or 505 response code on user traffic then
                # force <fastinter> check period.
                #
                # NOTES
                #
                # * This also requires 'check observe layer7' on the server
                #   options.
                # * When 'on-error' triggers a check, it will only occur after
                #   <fastinter> delay.
                # * Under the assumption of 100 client machines each
                #   healthchecking a service instance:
                #
                #     10 minute <inter>     -> 0.2qps
                #     30 second <downinter> -> 3.3qps
                #     30 second <fastinter> -> 3.3qps
                #
                # * The <downinter> checks should only occur when Zookeeper is
                #   down; ordinarily Nerve will quickly remove a backend if it
                #   fails its local healthcheck.
                # * The <fastinter> checks may occur when a service is generating
                #   errors but is still passing its healthchecks.
                ('default-server on-error fastinter error-limit 1'
                 ' inter {inter} downinter 30s fastinter 30s'
                 ' rise 1 fall 2'.format(inter=haproxy_inter)),
            ],

            'extra_sections': {
                'listen stats': [
                    'bind :%d' % synapse_tools_config['stats_port'],
                    'mode http',
                    'stats enable',
                    'stats uri /',
                    'stats refresh 1m',
                    'stats show-node',
                ]
            }
        }
    }
    return base_config


def get_backend_name(service_name, discover_type, advertise_type):
    if advertise_type == discover_type:
        return service_name
    else:
        return '%s.%s' % (service_name, advertise_type)


def generate_acls_for_service(
        service_name,
        discover_type,
        advertise_types,
        proxied_through,
        healthcheck_uri):
    frontend_acl_configs = []

    # check for proxied_through first, use_backend ordering matters
    if proxied_through:
        frontend_acl_configs.extend(
            [
                'acl is_status_request path {healthcheck_uri}'.format(
                    healthcheck_uri=healthcheck_uri,
                ),
                'acl request_from_proxy hdr_beg(X-Smartstack-Source) -i {proxied_through}'.format(
                    proxied_through=proxied_through,
                ),
                'acl proxied_through_backend_has_connslots connslots({proxied_through}) gt 0'.format(
                    proxied_through=proxied_through,
                ),
                'use_backend {proxied_through} if !is_status_request !request_from_proxy proxied_through_backend_has_connslots'.format(
                    proxied_through=proxied_through,
                ),
                'reqadd X-Smartstack-Destination:\ {service_name} if !is_status_request !request_from_proxy proxied_through_backend_has_connslots'.format(
                    service_name=service_name,
                ),
            ]
        )

    for advertise_type in advertise_types:
        if compare_types(discover_type, advertise_type) < 0:
            # don't create acls that downcast requests
            continue

        backend_identifier = get_backend_name(
            service_name=service_name,
            discover_type=discover_type,
            advertise_type=advertise_type,
        )

        # use connslots acl condition
        frontend_acl_configs.extend(
            [
                'acl {backend_identifier}_has_connslots connslots({backend_identifier}) gt 0'.format(
                    backend_identifier=backend_identifier,
                ),
                'use_backend {backend_identifier} if {backend_identifier}_has_connslots'.format(
                    backend_identifier=backend_identifier,
                ),
            ]
        )
    return frontend_acl_configs


def generate_configuration(synapse_tools_config, zookeeper_topology, services):
    synapse_config = generate_base_config(synapse_tools_config)
    available_locations = available_location_types()
    location_depth_mapping = {
        loc: depth
        for depth, loc in enumerate(available_locations)
    }
    available_locations = set(available_locations)
    proxies = [service_info['proxied_through'] for _, service_info in services if service_info.get('proxied_through') is not None]

    for (service_name, service_info) in services:
        proxy_port = service_info.get('proxy_port')
        if proxy_port is None:
            continue

        discover_type = service_info.get('discover', 'region')
        advertise_types = sorted(
            [
                advertise_typ
                for advertise_typ in service_info.get('advertise', ['region'])
                # don't consider invalid advertise types
                if advertise_typ in available_locations
            ],
            key=lambda typ: location_depth_mapping[typ],
            reverse=True,  # consider the most specific types first
        )
        if discover_type not in advertise_types:
            return {}

        base_haproxy_cfg = base_haproxy_cfg_for_service(
            service_name=service_name,
            service_info=service_info,
            zookeeper_topology=zookeeper_topology,
            synapse_tools_config=synapse_tools_config,
            is_proxy=service_name in proxies,
        )

        for advertise_type in advertise_types:
            config = copy.deepcopy(base_haproxy_cfg)

            backend_identifier = get_backend_name(service_name, discover_type, advertise_type)

            if advertise_type == discover_type:
                # Specify a proxy port to create a frontend for this service
                config['haproxy']['port'] = str(proxy_port)

            config['discovery']['label_filters'] = [
                {
                    'label': '%s:%s' % (advertise_type, get_current_location(advertise_type)),
                    'value': '',
                    'condition': 'equals',
                },
            ]

            config['haproxy']['backend_name'] = backend_identifier

            synapse_config['services'][backend_identifier] = config

        proxied_through = service_info.get('proxied_through')
        healthcheck_uri = service_info.get('healthcheck_uri', '/status')

        # populate the ACLs to route to the service backends
        synapse_config['services'][service_name]['haproxy']['frontend'].extend(
            generate_acls_for_service(
                service_name=service_name,
                discover_type=discover_type,
                advertise_types=advertise_types,
                proxied_through=proxied_through,
                healthcheck_uri=healthcheck_uri,
            )
        )

    return synapse_config


def base_haproxy_cfg_for_service(service_name, service_info, zookeeper_topology, synapse_tools_config, is_proxy):
    # If the service sets one timeout but not the other, set both
    # as per haproxy best practices.
    default_timeout = max(
        service_info.get('timeout_client_ms'),
        service_info.get('timeout_server_ms')
    )

    # Server options
    mode = service_info.get('mode', 'http')
    if mode == 'http':
        server_options = 'check port %d observe layer7 maxconn %d maxqueue %d'
    else:
        server_options = 'check port %d observe layer4 maxconn %d maxqueue %d'
    server_options = server_options % (
        synapse_tools_config['hacheck_port'],
        synapse_tools_config['maxconn_per_server'],
        synapse_tools_config['maxqueue_per_server'],
    )

    # Frontend options
    frontend_options = []
    timeout_client_ms = service_info.get(
        'timeout_client_ms', default_timeout
    )
    if timeout_client_ms is not None:
        frontend_options.append('timeout client %dms' % timeout_client_ms)

    frontend_options.append('bind /var/run/synapse/sockets/%s.sock' % service_name)

    if mode == 'http':
        frontend_options.append('capture request header X-B3-SpanId len 64')
        frontend_options.append('capture request header X-B3-TraceId len 64')
        frontend_options.append('capture request header X-B3-ParentSpanId len 64')
        frontend_options.append('capture request header X-B3-Flags len 10')
        frontend_options.append('capture request header X-B3-Sampled len 10')
        frontend_options.append('option httplog')
    elif mode == 'tcp':
        frontend_options.append('option tcplog')

    # backend options
    backend_options = []

    if is_proxy:
        backend_options.extend(
            [
                'acl is_status_request path {healthcheck_uri}'.format(
                    healthcheck_uri=service_info.get('healthcheck_uri', '/status'),
                ),
                'reqadd X-Smartstack-Source:\ {service_name} if !is_status_request'.format(
                    service_name=service_name,
                ),
            ]
        )

    extra_headers = service_info.get('extra_headers', {})
    for header, value in extra_headers.iteritems():
        backend_options.append('reqidel ^%s:.*' % (header))
    for header, value in extra_headers.iteritems():
        backend_options.append('reqadd %s:\ %s' % (header, value))

    # Listen options
    listen_options = []

    # hacheck healthchecking
    # Note that we use a dummy port value of '0' here because HAProxy is
    # passing in the real port using the X-Haproxy-Server-State header.
    # See SRV-1492 / SRV-1498 for more details.
    port = 0
    extra_healthcheck_headers = service_info.get('extra_healthcheck_headers', {})

    if len(extra_healthcheck_headers) > 0:
        healthcheck_base = 'HTTP/1.1'
        headers_string = healthcheck_base + ''.join(r'\r\n%s:\ %s' % (k, v) for (k, v) in extra_healthcheck_headers.iteritems())
    else:
        headers_string = ""

    healthcheck_uri = service_info.get('healthcheck_uri', '/status')
    healthcheck_string = r'option httpchk GET /%s/%s/%d/%s %s' % \
        (mode, service_name, port, healthcheck_uri.lstrip('/'), headers_string)

    healthcheck_string = healthcheck_string.strip()
    listen_options.append(healthcheck_string)

    listen_options.append('http-check send-state')

    if mode == 'tcp':
        listen_options.append('mode tcp')

    retries = service_info.get('retries')
    if retries is not None:
        listen_options.append('retries %d' % retries)

    allredisp = service_info.get('allredisp')
    if allredisp is not None and allredisp:
        listen_options.append('option allredisp')

    timeout_connect_ms = service_info.get('timeout_connect_ms')
    if timeout_connect_ms is not None:
        listen_options.append('timeout connect %dms' % timeout_connect_ms)

    timeout_server_ms = service_info.get(
        'timeout_server_ms', default_timeout
    )
    if timeout_server_ms is not None:
        listen_options.append('timeout server %dms' % timeout_server_ms)

    balance = service_info.get('balance')
    # Validations are done in config post-receive so invalid config should
    # be ignored
    if balance is not None and balance in ('leastconn', 'roundrobin'):
        listen_options.append('balance %s' % balance)

    discovery = {
        'method': 'zookeeper',
        'path': '/smartstack/global/%s' % service_name,
        'hosts': zookeeper_topology,
    }

    chaos = service_info.get('chaos')
    if chaos:
        frontend_chaos, discovery = chaos_options(chaos, discovery)
        frontend_options.extend(frontend_chaos)

    # Now write the actual synapse service entry
    service = {
        'default_servers': [],
        # See SRV-1190
        'use_previous_backends': False,
        'discovery': discovery,
        'haproxy': {
            'server_options': server_options,
            'frontend': frontend_options,
            'listen': listen_options,
            'backend': backend_options,
        }
    }

    return service


def chaos_options(chaos_dict, discovery_dict):
    """ Return a tuple of
    (additional_frontend_options, replacement_discovery_dict) """

    chaos_entries = merge_dict_for_my_grouping(chaos_dict)
    fail = chaos_entries.get('fail')
    delay = chaos_entries.get('delay')

    if fail == 'drop':
        return ['tcp-request content reject'], discovery_dict

    if fail == 'error_503':
        # No additional frontend_options, but use the
        # base (no-op) discovery method
        discovery_dict = {'method': 'base'}
        return [], discovery_dict

    if delay:
        return [
            'tcp-request inspect-delay {0}'.format(delay),
            'tcp-request content accept if WAIT_END'
        ], discovery_dict

    return [], discovery_dict


def merge_dict_for_my_grouping(chaos_dict):
    """ Given a dictionary where the top-level keys are
    groupings (ecosystem, habitat, etc), merge the subdictionaries
    whose values match the grouping that this host is in.
    e.g.

    habitat:
        sfo2:
            some_key: some_value
    runtimeenv:
        prod:
            another_key: another_value
        devc:
            foo_key: bar_value

    for a host in sfo2/prod, would return
        {'some_key': some_value, 'another_key': another_value}
    """
    result = {}
    for grouping_type, grouping_dict in chaos_dict.iteritems():
        my_grouping = get_my_grouping(grouping_type)
        entry = grouping_dict.get(my_grouping, {})
        result.update(entry)
    return result


def get_my_grouping(grouping_type):
    with open('/nail/etc/{0}'.format(grouping_type)) as fd:
        return fd.read().strip()


def main():
    my_config = get_config(os.environ.get('SYNAPSE_TOOLS_CONFIG_PATH', '/etc/synapse/synapse-tools.conf.json'))

    new_synapse_config = generate_configuration(
        my_config, get_zookeeper_topology(my_config['zookeeper_topology_path']), get_all_namespaces()
    )

    with tempfile.NamedTemporaryFile() as tmp_file:
        new_synapse_config_path = tmp_file.name
        with open(new_synapse_config_path, 'w') as fp:
            json.dump(new_synapse_config, fp, sort_keys=True, indent=4, separators=(',', ': '))

        # Match permissions that puppet expects
        os.chmod(new_synapse_config_path, 0644)

        # Restart synapse if the config files differ
        should_restart = not filecmp.cmp(new_synapse_config_path, my_config['config_file'])

        # Always swap new config file into place.  Our monitoring system
        # checks the config['config_file'] file age to ensure that it is
        # continually being updated.
        shutil.copy(new_synapse_config_path, my_config['config_file'])

        if should_restart:
            subprocess.check_call(my_config['synapse_restart_command'])
