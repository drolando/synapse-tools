import os
from base import HAProxyConfigPlugin


class Logging(HAProxyConfigPlugin):
    def __init__(self, service_name, service_info, synapse_tools_config):
        super(Logging, self).__init__(
            service_name, service_info, synapse_tools_config
        )

        global_enabled = self.synapse_tools_config.get('logging', {}).get('enabled', False)
        svc_enabled = self.plugins.get('logging', {}).get('enabled', False)
        self.enabled = svc_enabled or global_enabled

        self.plugin_opts = (
            self.plugins.get('logging', {}) if svc_enabled
            else self.synapse_tools_config.get('logging', {}) if global_enabled
            else {}
        )

    def global_options(self):
        if not self.enabled:
            return []

        lua_dir = self.synapse_tools_config['lua_dir']
        lua_file = os.path.join(lua_dir, 'log_requests.lua')
        map_dir = self.synapse_tools_config['map_dir']
        map_file = os.path.join(map_dir, 'ip_to_service.map')
        opts = [
            'lua-load %s' % lua_file,
            'setenv map_file %s' % map_file
        ]
        if 'sample_rate' in self.plugin_opts:
            sample_rate = str(self.plugin_opts['sample_rate'])
            opts.append('setenv sample_rate {0}'.format(sample_rate))
        return opts

    def frontend_options(self):
        return []

    def backend_options(self):
        if not self.enabled:
            return []
        return [
            'http-request lua.init_logging',
            'http-request lua.log_provenance'
        ]
