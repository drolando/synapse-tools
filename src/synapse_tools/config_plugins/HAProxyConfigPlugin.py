import abc

class HAProxyConfigPlugin(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def global_opts(self):
        return

    @abc.abstractmethod
    def frontend_opts(self):
        return

    @abc.abstractmethod
    def backend_opts(self):
        return


