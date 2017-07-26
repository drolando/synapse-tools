import os
from base import HAProxyConfigPlugin
from base import LuaPlugin


class Logging(HAProxyConfigPlugin, LuaPlugin):
    def __init__(self, lua_dir_path):
        super(Logging, self).__init__(lua_dir_path)

    def global_options(self, service_name, service_info):
        file_path = os.path.join(self.lua_dir_path, 'log_requests.lua')
        return ['lua-load %s' % file_path]

    def frontend_options(self, service_name, service_info):
        return ['http-request lua.log_src']

    def backend_options(self, service_name, service_info):
        return []
