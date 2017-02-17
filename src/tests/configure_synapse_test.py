import contextlib

import mock
import pytest

from synapse_tools import configure_synapse


@pytest.yield_fixture
def mock_get_current_location():
    def f(typ):
        return {
            'region': 'my_region',
            'superregion': 'my_superregion',
        }[typ]
    with mock.patch('synapse_tools.configure_synapse.get_current_location',
                    side_effect=f):
        yield


@pytest.yield_fixture
def mock_available_location_types():
    mock_types = [
        'runtimeenv',
        'ecosystem',
        'superregion',
        'region',
        'habitat',
    ]
    with contextlib.nested(
        mock.patch(
            'environment_tools.type_utils.available_location_types',
            return_value=mock_types,
        ),
        mock.patch(
            'synapse_tools.configure_synapse.available_location_types',
            return_value=mock_types,
        ),
    ):
        yield


def test_get_zookeeper_topology():
    m = mock.mock_open()
    with contextlib.nested(
            mock.patch('synapse_tools.configure_synapse.open', m, create=True),
            mock.patch('yaml.load', return_value=[['foo', 42]])):
        zk_topology = configure_synapse.get_zookeeper_topology('/path/to/fake/file')
    assert zk_topology == ['foo:42']
    m.assert_called_with('/path/to/fake/file')


def test_generate_configuration(mock_get_current_location, mock_available_location_types):
    actual_configuration = configure_synapse.generate_configuration(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
        zookeeper_topology=['1.2.3.4', '2.3.4.5'],
        services=[
            (
                'test_service',
                {
                    'proxy_port': 1234,
                    'healthcheck_uri': '/status',
                    'retries': 2,
                    'timeout_connect_ms': 2000,
                    'timeout_server_ms': 3000,
                    'extra_headers': {
                        'X-Mode': 'ro'
                    },
                    'extra_healthcheck_headers': {
                        'X-Mode': 'ro'
                    },
                    'balance': 'roundrobin',
                    'advertise': ['region', 'superregion'],
                    'discover': 'region',
                }
            )
        ]
    )

    actual_configuration_reversed_advertise = configure_synapse.generate_configuration(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
        zookeeper_topology=['1.2.3.4', '2.3.4.5'],
        services=[
            (
                'test_service',
                {
                    'proxy_port': 1234,
                    'healthcheck_uri': '/status',
                    'retries': 2,
                    'timeout_connect_ms': 2000,
                    'timeout_server_ms': 3000,
                    'extra_headers': {
                        'X-Mode': 'ro'
                    },
                    'extra_healthcheck_headers': {
                        'X-Mode': 'ro'
                    },
                    'balance': 'roundrobin',
                    'advertise': ['superregion', 'region'],
                    'discover': 'region',
                }
            )
        ]
    )

    expected_configuration = configure_synapse.generate_base_config(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'})
    )
    expected_configuration['services'] = {
        'test_service': {
            'default_servers': [],
            'use_previous_backends': False,
            'discovery': {
                'hosts': ['1.2.3.4', '2.3.4.5'],
                'method': 'zookeeper',
                'path': '/smartstack/global/test_service',
                'label_filters': [
                    {
                        'label': 'region:my_region',
                        'value': '',
                        'condition': 'equals',
                    },
                ],
            },
            'haproxy': {
                'listen': [
                    'option httpchk GET /http/test_service/0/status HTTP/1.1\\r\\nX-Mode:\\ ro',
                    'http-check send-state',
                    'retries 2',
                    'timeout connect 2000ms',
                    'timeout server 3000ms',
                    'balance roundrobin',
                ],
                'frontend': [
                    'timeout client 3000ms',
                    'bind /var/run/synapse/sockets/test_service.sock',
                    'capture request header X-B3-SpanId len 64',
                    'capture request header X-B3-TraceId len 64',
                    'capture request header X-B3-ParentSpanId len 64',
                    'capture request header X-B3-Flags len 10',
                    'capture request header X-B3-Sampled len 10',
                    'option httplog',
                    'acl test_service_has_connslots connslots(test_service) gt 0',
                    'use_backend test_service if test_service_has_connslots',
                    'acl test_service.superregion_has_connslots connslots(test_service.superregion) gt 0',
                    'use_backend test_service.superregion if test_service.superregion_has_connslots',
                ],
                'backend': [
                    'reqidel ^X-Mode:.*',
                    'reqadd X-Mode:\ ro',
                ],
                'port': '1234',
                'server_options': 'check port 6666 observe layer7 maxconn 50 maxqueue 10',
                'backend_name': 'test_service',
            },
        },
        'test_service.superregion': {
            'default_servers': [],
            'use_previous_backends': False,
            'discovery': {
                'hosts': ['1.2.3.4', '2.3.4.5'],
                'method': 'zookeeper',
                'path': '/smartstack/global/test_service',
                'label_filters': [
                    {
                        'label': 'superregion:my_superregion',
                        'value': '',
                        'condition': 'equals',
                    },
                ],
            },
            'haproxy': {
                'listen': [
                    'option httpchk GET /http/test_service/0/status HTTP/1.1\\r\\nX-Mode:\\ ro',
                    'http-check send-state',
                    'retries 2',
                    'timeout connect 2000ms',
                    'timeout server 3000ms',
                    'balance roundrobin',
                ],
                'frontend': [
                    'timeout client 3000ms',
                    'bind /var/run/synapse/sockets/test_service.sock',
                    'capture request header X-B3-SpanId len 64',
                    'capture request header X-B3-TraceId len 64',
                    'capture request header X-B3-ParentSpanId len 64',
                    'capture request header X-B3-Flags len 10',
                    'capture request header X-B3-Sampled len 10',
                    'option httplog',
                ],
                'backend': [
                    'reqidel ^X-Mode:.*',
                    'reqadd X-Mode:\ ro',
                ],
                'server_options': 'check port 6666 observe layer7 maxconn 50 maxqueue 10',
                'backend_name': 'test_service.superregion',
            },
        },
    }

    assert actual_configuration == expected_configuration
    assert actual_configuration_reversed_advertise == expected_configuration


def test_generate_configuration_single_advertise(mock_get_current_location, mock_available_location_types):
    actual_configuration = configure_synapse.generate_configuration(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
        zookeeper_topology=['1.2.3.4', '2.3.4.5'],
        services=[
            (
                'test_service',
                {
                    'proxy_port': 1234,
                    'healthcheck_uri': '/status',
                    'retries': 2,
                    'timeout_connect_ms': 2000,
                    'timeout_server_ms': 3000,
                    'extra_headers': {
                        'X-Mode': 'ro'
                    },
                    'extra_healthcheck_headers': {
                        'X-Mode': 'ro'
                    },
                    'balance': 'roundrobin',
                    'advertise': ['region'],
                    'discover': 'region',
                }
            )
        ]
    )

    actual_configuration_default_advertise = configure_synapse.generate_configuration(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
        zookeeper_topology=['1.2.3.4', '2.3.4.5'],
        services=[
            (
                'test_service',
                {
                    'proxy_port': 1234,
                    'healthcheck_uri': '/status',
                    'retries': 2,
                    'timeout_connect_ms': 2000,
                    'timeout_server_ms': 3000,
                    'extra_headers': {
                        'X-Mode': 'ro'
                    },
                    'extra_healthcheck_headers': {
                        'X-Mode': 'ro'
                    },
                    'balance': 'roundrobin',
                }
            )
        ]
    )

    expected_configuration = configure_synapse.generate_base_config(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'})
    )
    expected_configuration['services'] = {
        'test_service': {
            'default_servers': [],
            'use_previous_backends': False,
            'discovery': {
                'hosts': ['1.2.3.4', '2.3.4.5'],
                'method': 'zookeeper',
                'path': '/smartstack/global/test_service',
                'label_filters': [
                    {
                        'label': 'region:my_region',
                        'value': '',
                        'condition': 'equals',
                    },
                ],
            },
            'haproxy': {
                'listen': [
                    'option httpchk GET /http/test_service/0/status HTTP/1.1\\r\\nX-Mode:\\ ro',
                    'http-check send-state',
                    'retries 2',
                    'timeout connect 2000ms',
                    'timeout server 3000ms',
                    'balance roundrobin',
                ],
                'frontend': [
                    'timeout client 3000ms',
                    'bind /var/run/synapse/sockets/test_service.sock',
                    'capture request header X-B3-SpanId len 64',
                    'capture request header X-B3-TraceId len 64',
                    'capture request header X-B3-ParentSpanId len 64',
                    'capture request header X-B3-Flags len 10',
                    'capture request header X-B3-Sampled len 10',
                    'option httplog',
                    'acl test_service_has_connslots connslots(test_service) gt 0',
                    'use_backend test_service if test_service_has_connslots',
                ],
                'backend': [
                    'reqidel ^X-Mode:.*',
                    'reqadd X-Mode:\ ro',
                ],
                'port': '1234',
                'server_options': 'check port 6666 observe layer7 maxconn 50 maxqueue 10',
                'backend_name': 'test_service',
            },
        },
    }

    assert actual_configuration == expected_configuration
    assert actual_configuration_default_advertise == expected_configuration


def test_generate_configuration_empty(mock_available_location_types):
    actual_configuration = configure_synapse.generate_configuration(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
        zookeeper_topology=['1.2.3.4', '2.3.4.5'],
        services=[]
    )
    expected_configuration = configure_synapse.generate_base_config(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'})
    )
    assert actual_configuration == expected_configuration


def test_generate_configuration_with_proxied_through(mock_get_current_location, mock_available_location_types):
    actual_configuration = configure_synapse.generate_configuration(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
        zookeeper_topology=['1.2.3.4', '2.3.4.5'],
        services=[
            (
                'test_service',
                {
                    'proxy_port': 1234,
                    'healthcheck_uri': '/status',
                    'retries': 2,
                    'timeout_connect_ms': 2000,
                    'timeout_server_ms': 3000,
                    'extra_headers': {
                        'X-Mode': 'ro'
                    },
                    'extra_healthcheck_headers': {
                        'X-Mode': 'ro'
                    },
                    'balance': 'roundrobin',
                    'advertise': ['region'],
                    'discover': 'region',
                    'proxied_through': 'proxy_service',
                }
            ),
            (
                'proxy_service',
                {
                    'proxy_port': 5678,
                    'balance': 'roundrobin',
                    'advertise': ['region'],
                    'discover': 'region',
                }
            )
        ]
    )

    expected_configuration = configure_synapse.generate_base_config(
        synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'})
    )
    expected_configuration['services'] = {
        'proxy_service': {
            'default_servers': [],
            'use_previous_backends': False,
            'discovery': {
                'hosts': ['1.2.3.4', '2.3.4.5'],
                'method': 'zookeeper',
                'path': '/smartstack/global/proxy_service',
                'label_filters': [
                    {
                        'label': 'region:my_region',
                        'value': '',
                        'condition': 'equals',
                    },
                ],
            },
            'haproxy': {
                'listen': [
                    'option httpchk GET /http/proxy_service/0/status',
                    'http-check send-state',
                    'balance roundrobin',
                ],
                'frontend': [
                    'bind /var/run/synapse/sockets/proxy_service.sock',
                    'capture request header X-B3-SpanId len 64',
                    'capture request header X-B3-TraceId len 64',
                    'capture request header X-B3-ParentSpanId len 64',
                    'capture request header X-B3-Flags len 10',
                    'capture request header X-B3-Sampled len 10',
                    'option httplog',
                    'acl proxy_service_has_connslots connslots(proxy_service) gt 0',
                    'use_backend proxy_service if proxy_service_has_connslots',
                ],
                'backend': [
                    'acl is_status_request path /status',
                    'reqadd X-Smartstack-Source:\\ proxy_service if !is_status_request',
                ],
                'port': '5678',
                'server_options': 'check port 6666 observe layer7 maxconn 50 maxqueue 10',
                'backend_name': 'proxy_service',
            },
        },
        'test_service': {
            'default_servers': [],
            'use_previous_backends': False,
            'discovery': {
                'hosts': ['1.2.3.4', '2.3.4.5'],
                'method': 'zookeeper',
                'path': '/smartstack/global/test_service',
                'label_filters': [
                    {
                        'label': 'region:my_region',
                        'value': '',
                        'condition': 'equals',
                    },
                ],
            },
            'haproxy': {
                'listen': [
                    'option httpchk GET /http/test_service/0/status HTTP/1.1\\r\\nX-Mode:\\ ro',
                    'http-check send-state',
                    'retries 2',
                    'timeout connect 2000ms',
                    'timeout server 3000ms',
                    'balance roundrobin',
                ],
                'frontend': [
                    'timeout client 3000ms',
                    'bind /var/run/synapse/sockets/test_service.sock',
                    'capture request header X-B3-SpanId len 64',
                    'capture request header X-B3-TraceId len 64',
                    'capture request header X-B3-ParentSpanId len 64',
                    'capture request header X-B3-Flags len 10',
                    'capture request header X-B3-Sampled len 10',
                    'option httplog',
                    'acl is_status_request path /status',
                    'acl request_from_proxy hdr_beg(X-Smartstack-Source) -i proxy_service',
                    'acl proxied_through_backend_has_connslots connslots(proxy_service) gt 0',
                    'use_backend proxy_service if !is_status_request !request_from_proxy proxied_through_backend_has_connslots',
                    'reqadd X-Smartstack-Destination:\\ test_service if !is_status_request !request_from_proxy proxied_through_backend_has_connslots',
                    'acl test_service_has_connslots connslots(test_service) gt 0',
                    'use_backend test_service if test_service_has_connslots',
                ],
                'backend': [
                    'reqidel ^X-Mode:.*',
                    'reqadd X-Mode:\ ro',
                ],
                'port': '1234',
                'server_options': 'check port 6666 observe layer7 maxconn 50 maxqueue 10',
                'backend_name': 'test_service',
            },
        },
    }

    assert actual_configuration == expected_configuration


@contextlib.contextmanager
def setup_mocks_for_main():
    mock_tmp_file = mock.MagicMock()
    mock_file_cmp = mock.Mock()
    mock_copy = mock.Mock()
    mock_subprocess_check_call = mock.Mock()

    with contextlib.nested(
            mock.patch('synapse_tools.configure_synapse.get_zookeeper_topology'),
            mock.patch('synapse_tools.configure_synapse.get_all_namespaces'),
            mock.patch('synapse_tools.configure_synapse.generate_configuration'),
            mock.patch(
                'synapse_tools.configure_synapse.get_config',
                return_value=configure_synapse.set_defaults(
                    {'bind_addr': '0.0.0.0', 'config_file': '/etc/synapse/synapse.conf.json'}
                ),
            ),
            mock.patch('tempfile.NamedTemporaryFile', return_value=mock_tmp_file),
            mock.patch('synapse_tools.configure_synapse.open', create=True),
            mock.patch('json.dump'),
            mock.patch('os.chmod'),
            mock.patch('filecmp.cmp', mock_file_cmp),
            mock.patch('shutil.copy', mock_copy),
            mock.patch('subprocess.check_call', mock_subprocess_check_call)):
        yield(mock_tmp_file, mock_file_cmp, mock_copy, mock_subprocess_check_call)


def test_synapse_restarted_when_config_files_differ():
    with setup_mocks_for_main() as (
            mock_tmp_file, mock_file_cmp, mock_copy, mock_subprocess_check_call):

        # New and existing synapse configs differ
        mock_file_cmp.return_value = False

        configure_synapse.main()

        mock_copy.assert_called_with(
            mock_tmp_file.__enter__().name, '/etc/synapse/synapse.conf.json')
        mock_subprocess_check_call.assert_called_with(['service', 'synapse', 'restart'])


def test_synapse_not_restarted_when_config_files_are_identical():
    with setup_mocks_for_main() as (
            mock_tmp_file, mock_file_cmp, mock_copy, mock_subprocess_check_call):

        # New and existing synapse configs are identical
        mock_file_cmp.return_value = True

        configure_synapse.main()

        mock_copy.assert_called_with(
            mock_tmp_file.__enter__().name, '/etc/synapse/synapse.conf.json')
        assert not mock_subprocess_check_call.called


def test_chaos_delay(mock_get_current_location, mock_available_location_types):
    with mock.patch.object(configure_synapse, 'get_my_grouping') as grouping_mock:
        grouping_mock.return_value = 'my_ecosystem'
        actual_configuration = configure_synapse.generate_configuration(
            synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
            zookeeper_topology=['1.2.3.4'],
            services=[
                (
                    'test_service',
                    {
                        'proxy_port': 1234,
                        'chaos': {'ecosystem': {'my_ecosystem': {'delay': '300ms'}}}
                    }
                )
            ]
        )
        grouping_mock.assert_called_once_with('ecosystem')
    frontend = actual_configuration['services']['test_service']['haproxy']['frontend']
    assert 'tcp-request inspect-delay 300ms' in frontend
    assert 'tcp-request content accept if WAIT_END' in frontend


def test_chaos_drop(mock_get_current_location, mock_available_location_types):
    with mock.patch.object(configure_synapse, 'get_my_grouping') as grouping_mock:
        grouping_mock.return_value = 'my_ecosystem'
        actual_configuration = configure_synapse.generate_configuration(
            synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
            zookeeper_topology=['1.2.3.4'],
            services=[
                (
                    'test_service',
                    {
                        'proxy_port': 1234,
                        'chaos': {'ecosystem': {'my_ecosystem': {'fail': 'drop'}}}
                    }
                )
            ]
        )
        grouping_mock.assert_called_once_with('ecosystem')
    frontend = actual_configuration['services']['test_service']['haproxy']['frontend']
    assert 'tcp-request content reject' in frontend


def test_chaos_error_503(mock_get_current_location, mock_available_location_types):
    with mock.patch.object(configure_synapse, 'get_my_grouping') as grouping_mock:
        grouping_mock.return_value = 'my_ecosystem'
        actual_configuration = configure_synapse.generate_configuration(
            synapse_tools_config=configure_synapse.set_defaults({'bind_addr': '0.0.0.0'}),
            zookeeper_topology=['1.2.3.4'],
            services=[
                (
                    'test_service',
                    {
                        'proxy_port': 1234,
                        'chaos': {'ecosystem': {'my_ecosystem': {'fail': 'error_503'}}}
                    }
                )
            ]
        )
        assert actual_configuration['services']['test_service']['discovery']['method'] == 'base'
