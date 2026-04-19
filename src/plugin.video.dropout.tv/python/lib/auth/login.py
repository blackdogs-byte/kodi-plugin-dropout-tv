from ..logger import getLogger
logger = getLogger(__name__)

import requests
import urllib.parse
from bs4 import BeautifulSoup
from typing import Optional, Tuple

from ..constants import PluginConstants
from ..html import get_window_token
from .credentials import get_credentials

header_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
header_accept_language = 'en-US,en;q=0.9'

def to_login_form_data(email: str, password: str, authenticity_token: str, utf8: str) -> str:
  emailEncoded = urllib.parse.quote_plus(email)
  passwordEncoded = urllib.parse.quote_plus(password)
  authenticity_tokenEncoded = urllib.parse.quote_plus(authenticity_token)
  utf8Encoded = urllib.parse.quote_plus(utf8)

  formdata = f'email={emailEncoded}&authenticity_token={authenticity_tokenEncoded}&utf8={utf8Encoded}&password={passwordEncoded}'
  logger.debug(f'LOGIN data is: "{formdata}"')
  return formdata

def login(constants: PluginConstants, session: requests.Session) -> Tuple[Optional[str], str]:
  err, email, password = get_credentials(constants)
  if err:
    return err, ""
  
  host = constants.url_host_web_app
  baseUrl = f'https://{host}/'
  loginUrl = f'{baseUrl}login'

  # VISIT SIGN-IN PAGE
  headers = {
    'Host': host,
    'User-Agent': header_user_agent,
    'Accept-Language': header_accept_language,
    'Upgrade-Insecure-Requests': '1',
    'Referer': baseUrl,
  }
  r = session.get(loginUrl, headers=headers)
  logger.debug(f'GET {loginUrl}\nRETURNED\n\tHEADERS: {r.headers}\n\tBODY: {r.text}')

  logger.debug("Extracting authenticity_token and utf hidden input values...")
  soup = BeautifulSoup(r.text, "html.parser")

  authenticity_token = soup.select_one("input[name='authenticity_token']")["value"]
  utf8 = soup.select_one("input[name='utf8']")["value"]

  # LOGIN FORM
  formdata = to_login_form_data(email, password, authenticity_token, utf8)

  headers = {
    'Host': host,
    'User-Agent': header_user_agent,
    'Accept-Language': header_accept_language,
    'Upgrade-Insecure-Requests': '1',
    'Origin': baseUrl,
    'Referer': loginUrl,
    "Content-Type": 'application/x-www-form-urlencoded',
    "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
  }
  r = session.post(loginUrl, headers=headers, data=formdata)
  # Should redirect to /browse
  logger.debug(f'POST {loginUrl}\nREDIRECTED to {r.url} and\nRETURNED\n\tHEADERS: {r.headers}\nBODY:\n {r.text}')
  # that page then contains window.TOKEN as expected for 'after login'...
  return get_window_token(constants, r.text)
