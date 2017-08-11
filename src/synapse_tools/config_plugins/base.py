import abc


class HAProxyConfigPlugin(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, plugin_opts, service_name,
                 service_info, synapse_tools_config):
        """
        Initializes plugin base class
        :param dict plugin_opts: dictionary of plugin options
        :param str service_name: name of service
        :param dict service_info: dictionary of service config info
        :param dict synapse_tools_config: dictionary of synapse tools
                 config options
        """
        self.plugin_opts = plugin_opts
        self.service_name = service_name
        self.service_info = service_info
        self.synapse_tools_config = synapse_tools_config

    @abc.abstractmethod
    def global_options(self):
        """
        Options for HAProxy configuration global section
        :return: list of strings corresponding to distinct
                 lines in HAProxy config global
        """
        return

    @abc.abstractmethod
    def frontend_options(self):
        """
        Options for HAProxy configuration frontend section
        :return: list of strings representing distinct
                 lines in HAProxy config frontend
        """
        return

    @abc.abstractmethod
    def backend_options(self):
        """
        Options for HAProxy configuration backend section
        :return: list of strings representing distinct
                 lines in HAProxy config backend
        """
        return
