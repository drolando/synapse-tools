import os
from base import HAProxyConfigPlugin
from base import LuaPlugin


class PathBasedRouting(HAProxyConfigPlugin, LuaPlugin):
    def __init__(self, lua_dir_path):
        super(PathBasedRouting, self).__init__(lua_dir_path)

    def global_options(self, service_name, service_info):
        file_path = os.path.join(self.lua_dir_path, 'path_based_routing.lua')
        return ['lua-load %s' % file_path]

    def frontend_options(self, service_name, service_info):
        return [
            'http-request set-var(txn.backend_name) lua.get_backend',
            'use_backend %[var(txn.backend_name)]'
        ]

    def backend_options(self, service_name, service_info):
        return []
