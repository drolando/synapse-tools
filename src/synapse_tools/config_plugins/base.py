import abc


class HAProxyConfigPlugin(object):
    __metaclass__ = abc.ABCMeta

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
