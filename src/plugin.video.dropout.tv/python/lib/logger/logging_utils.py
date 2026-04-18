from ..logger import getLogger
logger = getLogger(__name__)

import xbmcplugin

from ..constants import PluginConstants

def token_or_stars(constants: PluginConstants, token: str):
  """
  Returns the token, if token logging is enabled, else returns ***
  """
  log_token = "true" == xbmcplugin.getSetting(constants.addon_handle, 'logtokens').strip().lower()
  return token if log_token else "***"
