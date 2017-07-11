from HAProxyConfigPlugin import HAProxyConfigPlugin

class ProvidenceLogging(HAProxyConfigPlugin):
    def global_opts(self):
        return ['lua-load ~/pg/synapse-tools/src/synapse_tools/lua_scripts/log_requests.lua']

    def frontend_opts(self):
        return ['http-request lua.log_src']

    def backend_opts(self):
        return ['http-request lua.log_dest']

if __name__ == "__main__":
    print "Is subclass: ", issubclass(ProvidenceLogging, HAProxyConfigPlugin)
