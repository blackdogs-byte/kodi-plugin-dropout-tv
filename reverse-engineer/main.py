# run with
# python /main.py --log-level DEBUG --email <your-email> --password <your-password>

### BEGIN SETUP UTILITIES ###

import logging
import sys

root = logging.getLogger()
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
root.addHandler(handler)

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

logging.basicConfig(
  filename='app.log',
  filemode='w',
  format='%(name)s %(levelname)s %(message)s',
  level=args.log_level
)

### END SETUP UTILITIES ###

import requests
import urllib.parse
from bs4 import BeautifulSoup
import re
import jwt

host = f'watch.dropout.tv'
baseUrl = f'https://{host}/'
loginUrl = f'{baseUrl}login'

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

if __name__ == "__main__":
  logger.warning("Hardcoded playalong to log into dropout TV")

  ########### Integrated Auth flow? ###########
  session = requests.Session()

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

  logger.debug("Extracting authenticity_token and utf hiden input values...")
  soup = BeautifulSoup(r.text, "html.parser")
  # authenticity_token
  authenticity_token = soup.select_one("input[name='authenticity_token']")["value"]
  utf8 = soup.select_one("input[name='utf8']")["value"]

  # LOGIN FORM
  formdata = to_login_form_data(args.email, args.password, authenticity_token, utf8)

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
  window_token = get_window_token(r.text)
  if not window_token:
    exit(1)
  logging.debug(f"Decoding token...")
  res = jwt.decode(window_token, options={"verify_signature": False, "verify_exp": True})
  logging.info(f"Token content: {res}")

  # TODO: what token(s) are used to play a video
