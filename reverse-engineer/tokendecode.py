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
parser.add_argument('-t', '--token', action='store', dest='token', help='jwt token')
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

import jwt

if __name__ == "__main__":
  token = args.token
  logging.info(f"Decoding token: '{token}'")
  res = jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
  logging.info(f"Token content: {res}")
