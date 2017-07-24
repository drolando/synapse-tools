from collections import OrderedDict
from logging import Logging
from path_based_routing import PathBasedRouting

PLUGIN_MAP = OrderedDict([
    ('logging', Logging),
    ('path_based_routing', PathBasedRouting)
])
