from ..logger import getLogger
logger = getLogger(__name__)

import xbmcgui
import xbmcplugin

from typing import Tuple

from ..constants import PluginConstants

def play_video(constants: PluginConstants, videoUrl: str) -> Tuple[bool, xbmcgui.ListItem]:
  listitem = xbmcgui.ListItem(path=videoUrl, offscreen=True)

  # Prevent HTTP HEAD request from Kodi core
  listitem.setContentLookup(False)

  # Set mimetype based on stream type
  if '.m3u8' in videoUrl:
    listitem.setMimeType('application/vnd.apple.mpegurl')
  elif '.mpd' in videoUrl:
    listitem.setMimeType('application/dash+xml')
  else:
    listitem.setMimeType('application/dash+xml')

  listitem.setProperty('inputstream', 'inputstream.adaptive')
  # Don't set manifest_type - let inputstream.adaptive auto-detect (deprecated anyway)

  return True, listitem
