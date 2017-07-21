from base import HAProxyConfigPlugin
from base import LuaPlugin


class PathBasedRouting(HAProxyConfigPlugin, LuaPlugin):
    def __init__(self, lua_scripts_path):
        super(PathBasedRouting, self).__init__(lua_scripts_path)

    def global_options(self, service_name, service_info):
        return ['lua-load %spath_based_routing.lua' % self.lua_scripts_path]

    def frontend_options(self, service_name, service_info):
        return [
            'http-request set-var(txn.backend_name) lua.get_backend',
            'use_backend %[var(txn.backend_name)]'
        ]

    def backend_options(self, service_name, service_info):
        return []
