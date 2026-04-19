# run with
# python /main.py --log-level DEBUG --email <your-email> --password <your-password>

### BEGIN SETUP UTILITIES ###

from typing import Optional, Tuple

import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

formatter = logging.Formatter(fmt='%(name)s %(levelname)s %(message)s')

stdOutHandler = logging.StreamHandler(sys.stdout)
stdOutHandler.setLevel(logging.DEBUG)
stdOutHandler.setFormatter(formatter)
root.addHandler(stdOutHandler)
fileHandler = logging.FileHandler(filename='app.log', mode='w')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
root.addHandler(fileHandler)

logger = logging.getLogger(__name__)

import argparse
import argcomplete

parser = argparse.ArgumentParser()
parser.add_argument('-ll', '--log-level', action='store', dest='log_level', help='Log Level', default='INFO')
parser.add_argument('-e', '--email', action='store', dest='email', help='email address')
parser.add_argument('-p', '--password', action='store', dest='password', help='Password')
argcomplete.autocomplete(parser)

args = None
try:
    args = parser.parse_args()
except ImportError:
    logger.critical("Import error, there are missing dependencies to install.  'apt-get install python3-argcomplete "
          "&& activate-global-python-argcomplete3' may solve")
except AttributeError:
    parser.print_help()
except Exception as err:
    logger.error("Error:", err)

if args is None:
  exit(1)

root.setLevel(args.log_level)

### END SETUP UTILITIES ###

import requests
import urllib.parse
from bs4 import BeautifulSoup
import re
import jwt

host = f'watch.dropout.tv'
baseUrl = f'https://{host}/'
loginUrl = f'{baseUrl}login'
logoutUrl = f'{baseUrl}logout'
aVideoUrl = f'{baseUrl}parlor-room/season:1/videos/wavelength'

header_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
header_accept_language = 'en-US,en;q=0.9'

def get_window_token(text: str) -> str | None:
  """
  Search for the value of window.TOKEN within the text.

  Usually this value is present within the html requests to dropout.tv after being logged in.
  """
  match = re.search(r'window\.TOKEN\s*=\s*"([^"]+)"', text)
  token = match.group(1) if match else None

  logger.info(f"Retreived window.TOKEN: {token}")
  return token

def to_login_form_data(email: str, password: str, authenticity_token: str, utf8: str) -> str:
  emailEncoded = urllib.parse.quote_plus(email)
  passwordEncoded = urllib.parse.quote_plus(password)
  authenticity_tokenEncoded = urllib.parse.quote_plus(authenticity_token)
  utf8Encoded = urllib.parse.quote_plus(utf8)

  formdata = f'email={emailEncoded}&authenticity_token={authenticity_tokenEncoded}&utf8={utf8Encoded}&password={passwordEncoded}'
  logger.debug(f'LOGIN data is: "{formdata}"')
  return formdata

def logout(session: requests.Session, csrfToken: str):
  logger.info('LOGGING OUT')
  formdata = f'authenticity_token={urllib.parse.quote_plus(csrfToken)}'
  headers = {
    'Host': host,
    'User-Agent': header_user_agent,
    'Accept-Language': header_accept_language,
    'Upgrade-Insecure-Requests': '1',
    'Referer': baseUrl,
    "Content-Type": 'application/x-www-form-urlencoded',
    "Accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
  }
  r = session.post(logoutUrl, headers=headers, data=formdata)
  logger.debug(f'POST {logoutUrl}\nREDIRECTED to {r.url} and\nRETURNED\n\tHEADERS: {r.headers}')

def login(session: requests.Session, email, password) -> Tuple[Optional[str], str]:
   # VISIT SIGN-IN PAGE
  headers = {
    'Host': host,
    'User-Agent': header_user_agent,
    'Accept-Language': header_accept_language,
    'Upgrade-Insecure-Requests': '1',
    'Referer': baseUrl,
  }
  r = session.get(loginUrl, headers=headers)
  # logger.debug(f'GET {loginUrl}\nRETURNED\n\tHEADERS: {r.headers}\n\tBODY: {r.text}')
  logger.debug(f'GET {loginUrl}\nRETURNED\n\tHEADERS: {r.headers}')

  logger.debug("Extracting authenticity_token and utf hiden input values...")
  soup = BeautifulSoup(r.text, "html.parser")
  # authenticity_token
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
  logger.debug(f'POST {loginUrl}\nREDIRECTED to {r.url} and\nRETURNED\n\tHEADERS: {r.headers}')

  window_token = get_window_token(r.text)
  csrf_token: str = soup.select_one("meta[name='csrf-token']")["content"]
  if window_token:
    logging.debug(f"Decoding token...")
    res = jwt.decode(window_token, options={"verify_signature": False, "verify_exp": True})
    logging.info(f"Token content: {res}")
  else:
    # log response body on error
    logger.debug(f'POST {loginUrl} RETURNED BODY:\n {r.text}')
  return window_token, csrf_token

def get_video_iframe_from_text(text: str) -> None | str:
  """
  Search for the iframe with title='Video Player'
  """
  match = re.search(r'"(https:\/\/embed\.vhx\.tv\/videos\/\S+)"', text)
  url = match.group(1) if match else None
  if not isinstance(url, str):
    logger.error("Video HTML does not have embed.vhx.tv video url")
    return None

  logger.info(f"Extracted embed.vhx.tv url '{url}'")
  return url

def play_video(session: requests.Session):
  ########### Play Video flow ###########
  # TODO: Continue here with one video to get the hls streams to vod-adaptive-ak.vimeocdn.com links

  # VISIT SPECIFIC VIDEO PAGE
  headers = {
    'Host': host,
    'User-Agent': header_user_agent,
    'Accept-Language': header_accept_language,
    'Upgrade-Insecure-Requests': '1',
    'Referer': baseUrl,
  }
  r = session.get(aVideoUrl, headers=headers)
  logger.debug(f'GET {loginUrl}\nRETURNED\n\tHEADERS: {r.headers}')

  iframeUrl = get_video_iframe_from_text(r.text)
  if not iframeUrl:
    # log response body on error
    logger.debug(f'GET {loginUrl}\nRETURNED BODY: {r.text}')
    return

  # CALL IFRAME
  headers = {
    'User-Agent': header_user_agent,
    'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': header_accept_language,
    'Upgrade-Insecure-Requests': '1',
    'Referer': baseUrl,
    'Sec-Fetch-Dest': 'iframe',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
  }
  r = session.get(iframeUrl, headers=headers)
  logger.debug(f'GET {iframeUrl}\nRETURNED\n\tHEADERS: {r.headers}\n\tBODY: {r.text}')

if __name__ == "__main__":
  logger.warning(">>>>>>> Hardcoded playalong to log into dropout TV and retreive video stream <<<<<<<")
  session = requests.Session()
  csrfToken: Optional[str] = None

  try:
    windowToken, csrfToken = login(session, args.email, args.password)
    play_video(session)

  finally:
    logger.info(">>>>>>> Running clean-up <<<<<<<")
    if csrfToken:
      logout(session, csrfToken)
