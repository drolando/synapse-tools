import os
from base import HAProxyConfigPlugin


class Logging(HAProxyConfigPlugin):
    def __init__(self, service_name, service_info, synapse_tools_config):
        self.service_name = service_name
        self.service_info = service_info
        self.synapse_tools_config = synapse_tools_config

    def global_options(self):
        lua_dir = self.synapse_tools_config['lua_dir']
        file_path = os.path.join(lua_dir, 'log_requests.lua')
        return ['lua-load %s' % file_path]

    def frontend_options(self):
        return ['http-request lua.log_src']

    def backend_options(self):
        return []
