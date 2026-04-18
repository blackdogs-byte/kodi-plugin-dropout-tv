from ..logger import getLogger
logger = getLogger(__name__)

from typing import Optional
import xbmcvfs
import xbmcplugin

from ..constants import PluginConstants

def _get_token_file_path(constants: PluginConstants):
  """
  Gets filepath for token store.
  """
  path = xbmcplugin.getSetting(constants.addon_handle, 'tokenfile')
  logger.debug(f"Token file path is '{path}'.")
  return path

def store_token(constants: PluginConstants, token: str):
  """
  Store token to filesystem.
  """
  logger.debug(f"Storing token to filesystem...")
  path = _get_token_file_path(constants)

  with xbmcvfs.File(path, 'w') as f:
    f.write(token)
    logger.info(f"Stored token to '{path}'.")

def load_token(constants: PluginConstants) -> Optional[str]:
  """
  Load token from filesystem.
  
  If file does not exist, returns None.
  """
  logger.debug(f"Loading token from filesystem")
  path = _get_token_file_path(constants)

  if xbmcvfs.exists(path):
    logger.debug(f"Token file '{path}' exists")
    with xbmcvfs.File(path, 'r') as f:
      token = f.read()
      logger.info(f"Loaded token from '{path}'.")
      return token
  else:
    logger.info(f"No token file found at '{path}'.")
  return None
