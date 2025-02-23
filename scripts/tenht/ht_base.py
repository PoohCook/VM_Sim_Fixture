from modules.tenextension import BaseExtension
from modules.tenconfig import ConfigInterface
from modules.legacy.extensionMessages import *
from modules.tenio import *
from .ht_interface import HtInterface


class HtBase(BaseExtension, IoInterface, ConfigInterface, HtInterface):
    pass
