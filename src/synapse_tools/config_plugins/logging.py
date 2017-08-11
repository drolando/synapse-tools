import os
from base import HAProxyConfigPlugin


class Logging(HAProxyConfigPlugin):

    def global_options(self):
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
            opts.append('setenv sample_rate %s' % sample_rate)
        return opts

    def frontend_options(self):
        return [
            'http-request lua.load_map',
            'http-request lua.log_src'
        ]

    def backend_options(self):
        return ['http-request lua.log_dest']
