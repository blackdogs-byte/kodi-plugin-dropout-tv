from ..logger import getLogger
logger = getLogger(__name__)

from typing import Optional, Tuple

import xbmcplugin
import xbmcaddon

from ..constants import PluginConstants

def get_credentials(constants: PluginConstants) -> Tuple[Optional[str], str, str]:
  """
  Get Credentials from settings, or opens settings if they are not yet set.

  Returns: [ERR, email, password]
  """
  email = xbmcplugin.getSetting(constants.addon_handle, 'email')
  password = xbmcplugin.getSetting(constants.addon_handle, 'password')
  if not email or not password:
    xbmcaddon.Addon().openSettings()
    return "Missing Credentials", "", ""
  else:
    return None, email, password
