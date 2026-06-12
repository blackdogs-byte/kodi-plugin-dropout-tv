from ..logger import getLogger, token_or_stars
logger = getLogger(__name__)

import re
from typing import Tuple, Optional

from ..constants import PluginConstants

def get_window_token(constants: PluginConstants, text: str) -> Tuple[Optional[str], str]:
  """
  Search for the value of window.TOKEN within the text.

  NOTE: An anonymous token is already present BEFORE logging in.
  """
  match = re.search(r'window\.TOKEN\s*=\s*"([^"]+)"', text)
  if not match:
    return "Text does not contain window.TOKEN", ""
  token = match.group(1)
  if not token:
    return "Text does not contain window.TOKEN (no match group)", ""

  logger.info(f"Retreived window.TOKEN: {token_or_stars(constants, token)}")
  return None, token
