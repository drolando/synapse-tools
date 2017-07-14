from HAProxyConfigPlugin import HAProxyConfigPlugin
from HAProxyConfigPlugin import LUA_SCRIPTS_PATH

class ProvidenceLogging(HAProxyConfigPlugin):
    def global_opts(self, service_name, service_info):
        return ['lua-load %slog_requests.lua' % LUA_SCRIPTS_PATH]

    def frontend_opts(self, service_name, service_info):
        return ['http-request lua.log_src']

    def backend_opts(self, service_name, service_info):
        return ['http-request lua.log_dest']
