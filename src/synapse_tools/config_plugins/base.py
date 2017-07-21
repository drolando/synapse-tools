import abc


class HAProxyConfigPlugin(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def global_options(self, service_name, service_info):
        """
        Options for HAProxy configuration global section
        :param str service_name: name of service
        :param dict service_info: dictionary of service config info
        :return: list of strings corresponding to distinct
                 lines in HAProxy config global
        """
        return

    @abc.abstractmethod
    def frontend_options(self, service_name, service_info):
        """
        Options for HAProxy configuration frontend section
        :param str service_name: name of service
        :param dict service_info: dictionary of service config info
        :return: list of strings representing distinct
                 lines in HAProxy config frontend
        """
        return

    @abc.abstractmethod
    def backend_options(self, service_name, service_info):
        """
        Options for HAProxy configuration backend section
        :param str service_name: name of service
        :param dict service_info: dictionary of service config info
        :return: list of strings representing distinct
                 lines in HAProxy config backend
        """
        return


class LuaPlugin(object):
    def __init__(self, lua_scripts_path):
        self.lua_scripts_path = lua_scripts_path
