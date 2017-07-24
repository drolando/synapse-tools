from base import HAProxyConfigPlugin
from base import LuaPlugin


class Logging(HAProxyConfigPlugin, LuaPlugin):
    def __init__(self, lua_scripts_path):
        super(Logging, self).__init__(lua_scripts_path)

    def global_options(self, service_name, service_info):
        return ['lua-load %slog_requests.lua' % self.lua_scripts_path]

    def frontend_options(self, service_name, service_info):
        return ['http-request lua.log_src']

    def backend_options(self, service_name, service_info):
        return []
