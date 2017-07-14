import abc

LUA_SCRIPTS_PATH = '~/pg/synapse-tools/src/synapse_tools/lua_scripts/'


class HAProxyConfigPlugin(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def global_opts(self, service_name, service_info):
        return

    @abc.abstractmethod
    def frontend_opts(self, service_name, service_info):
        return

    @abc.abstractmethod
    def backend_opts(self, service_name, service_info):
        return
