from ..logger import getLogger
logger = getLogger(__name__)

import requests
from typing import Optional, Tuple

from .login import login

from ..constants import PluginConstants
from ..html import get_window_token
from ..cookies import store_cookies_from_session

def get_bearer_token(constants: PluginConstants, session: requests.Session) -> Tuple[Optional[str], str]:
  """
  Wrapper to get Bearer Token.

  Uses existing session from FS - Logs back in if necessary
  """

  # TODO: Read Token from FS first, if not 'expired' can use it.
  logger.info(f"GET Browse page to get session cookies...")
  r = session.get(f'https://{constants.url_host_web_app}/browse')

  # TODO: If response != 200
  store_cookies_from_session(constants, session)

  err, bearerToken = get_window_token(constants, r.text)
  # TODO: window.TOKEN can be an anonymous token, so we will never log in (yet). Need to figure out a different way to check whether or not we are logged in. Maybe token inspection, since we already want to check expiry anyways.
  if not err:
    return None, bearerToken

  logger.debug(f"Error when tryint to get bearer token: {err}, falling back to login")

  err, token = login(constants, session)
  if err:
    return err, ""

  # TODO: Store token to FS
  return None, token
