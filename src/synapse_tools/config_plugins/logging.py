import os
from base import HAProxyConfigPlugin


class Logging(HAProxyConfigPlugin):
    def __init__(self, service_name, service_info, synapse_tools_config):
        super(Logging, self).__init__(
            service_name, service_info, synapse_tools_config
        )
        global_enabled = synapse_tools_config.get('logging', False)
        svc_enabled = service_info.get('plugins', {}).get('logging', False)

        self.enabled = svc_enabled or global_enabled

    def global_options(self):
        if not self.enabled:
            return []

        lua_dir = self.synapse_tools_config['lua_dir']
        lua_file = os.path.join(lua_dir, 'log_requests.lua')
        map_dir = self.synapse_tools_config['map_dir']
        map_file = os.path.join(map_dir, 'ip_to_service.map')
        return [
            'lua-load %s' % lua_file,
            'setenv map_file %s' % map_file
        ]

    def frontend_options(self):
        if not self.enabled:
            return []

        return [
            'http-request lua.load_map',
            'http-request lua.log_src'
        ]

    def backend_options(self):
        if not self.enabled:
            return []

        return ['http-request lua.log_dest']
