from ..logger import getLogger
logger = getLogger(__name__)

import requests
from typing import Optional, Tuple, List, TypedDict, cast

try:  # Python 3
  import jwt
except ImportError:  # Python 2
  # The package is named pyjwt in Kodi: https://github.com/lottaboost/script.module.pyjwt/pull/1
  import pyjwt as jwt # pyright: ignore[reportMissingImports]

from .login import login

from ..constants import PluginConstants
from ..html import get_window_token
from ..fs import store_cookies_from_session, load_token, store_token

def is_token_valid_login(token: str) -> bool:
  """
  Check the JWT token for 'user_id' field and not being expired.

  Returns TRUE, when good to use for API calls

  Returns FALSE, if not logged in or expired
  """
  try:
    content: TokenContents = cast(TokenContents, jwt.decode(token,options={"verify_signature": False, "verify_exp": True}))
    if content.get("user_id"):
      logger.debug(f"Token is valid")
      return True
    logger.debug(f"Token does not contain 'user_id'")
  except jwt.ExpiredSignatureError:
    logger.debug(f"Token expired")
  except jwt.InvalidTokenError:
    logger.debug(f"Token invalid")
  return False

def get_bearer_token(constants: PluginConstants, session: requests.Session) -> Tuple[Optional[str], str]:
  """
  Wrapper to get Bearer Token.

  Uses existing session from FS - Logs back in if necessary
  """
  ### ATTEMPT 1 -> Load existing token from filesystem ###
  token = load_token(constants)
  if token and is_token_valid_login(token):
    return None, token

  ### ATTEMPT 2 -> Use existing session, take browse page window token ###
  logger.info(f"GET Browse page to get session cookies...")
  r = session.get(f'https://{constants.url_host_web_app}/browse')

  err, token = get_window_token(constants, r.text)
  if not err and is_token_valid_login(token):
    store_cookies_from_session(constants, session)
    store_token(constants, token)
    return None, token

  ### ATTEMPT 3 -> Full Login procedure ###
  logger.debug(f"Error when trying to get bearer token: {err}, falling back to login")

  err, token = login(constants, session)
  if err:
    return err, ""
  if not is_token_valid_login(token):
    return "Retreived Token is not valid", ""

  store_cookies_from_session(constants, session)
  store_token(constants, token)
  return None, token

class TokenContents(TypedDict, total=False):
  """
  Decoded contents of the window.token (JWT)
  """
  app_id: int
  exp: int
  nonce: str
  scopes: List[str]
  session_id: str
  user_id: Optional[int]
  """present, when logged in."""
