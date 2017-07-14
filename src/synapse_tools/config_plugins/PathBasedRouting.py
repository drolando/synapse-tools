from HAProxyConfigPlugin import HAProxyConfigPlugin
from HAProxyConfigPlugin import LUA_SCRIPTS_PATH


class PathBasedRouting(HAProxyConfigPlugin):
    def global_opts(self, service_name, service_info):
        return ['lua-load %spath_based_routing.lua' % LUA_SCRIPTS_PATH]

    def frontend_opts(self, service_name, service_info):
        return [
            'http-request set-var(txn.backend_name) lua.get_backend',
            'use_backend %[var(txn.backend_name)]'
        ]

    def backend_opts(self, service_name, service_info):
        return []
