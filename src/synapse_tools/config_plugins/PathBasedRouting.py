from HAProxyConfigPlugin import HAProxyConfigPlugin

class PathBasedRouting(HAProxyConfigPlugin):
    def global_opts(self):
        return ['lua-load ~/pg/synapse-tools/src/synapse_tools/lua_scripts/path_based_routing.lua']

    def frontend_opts(self):
        return [
            'http-request set-var(txn.backend_name) lua.get_backend',
            'use_backend %[var(txn.backend_name)]'
        ]

    def backend_opts(self):
        return []
