from ..logger import getLogger, logResponse
logger = getLogger(__name__)

import requests
import re
import json
from typing import Tuple, Optional
from bs4 import BeautifulSoup
from html import unescape

from ..constants import PluginConstants

def get_video(constants: PluginConstants, session: requests.Session, droupoutHref: str) -> Tuple[Optional[str], str]:
  """
  Calls dropout.tv HTML for video, extracts config_url, fetches stream manifest.
  """
  logger.debug(f"Calling video page: {droupoutHref}")
  r = session.get(droupoutHref)
  logResponse(constants, r)
  
  err, iframeUrl = get_video_iframe_from_text(constants, r.text)
  if err:
    return err, ""
  
  # Unescape HTML entities in URL (e.g. &amp; -> &)
  iframeUrl = unescape(iframeUrl)
  
  logger.debug(f"Fetching iframe: {iframeUrl}")
  referer = f'https://{constants.url_host_web_app}/'
  r = session.get(iframeUrl, headers={'Referer': referer})
  logResponse(constants, r)
  
  err, streamUrl = extract_stream_from_iframe(constants, session, r.text)
  return err, streamUrl


def get_video_iframe_from_text(constants: PluginConstants, text: str) -> Tuple[Optional[str], str]:
  """
  Search for the embed.vhx.tv iframe in the page HTML.
  Tries multiple selectors for compatibility.
  """
  soup = BeautifulSoup(text, "html.parser")

  # Try title='Video Player' first (old site)
  iframe_tag = soup.select_one("iframe[title='Video Player']")
  
  # Fallback: find any iframe with embed.vhx.tv in src
  if not iframe_tag:
    for iframe in soup.find_all("iframe"):
      src = iframe.get("src", "")
      if "embed.vhx.tv" in src:
        iframe_tag = iframe
        break
  
  # Fallback: search raw HTML for embed.vhx.tv URL
  if not iframe_tag:
    match = re.search(r'https?://embed\.vhx\.tv/videos/\d+[^"\'>\s]+', text)
    if match:
      return None, match.group(0)
    return "HTML does not contain embed.vhx.tv iframe", ""

  href = iframe_tag.get("src", "")
  if not href or "embed.vhx.tv" not in href:
    return "HTML does not contain valid iframe src", ""

  logger.info(f"Extracted iframe href '{href[:120]}'")
  return None, href


def _extract_url_from_files(files: dict) -> str:
  """
  Search through Vimeo files dict for a playable stream URL.
  Prefers HLS .m3u8 over DASH .json playlists.
  """
  # First try hls > cdns > first_cdn > url (m3u8)
  hls = files.get('hls', {})
  if isinstance(hls, dict):
    cdns = hls.get('cdns', {})
    for cdn_name, cdn_data in cdns.items():
      if isinstance(cdn_data, dict):
        url = cdn_data.get('url', '')
        if url and '.m3u8' in url:
          return url
  
  # Then try dash > cdns > first_cdn > url
  dash = files.get('dash', {})
  if isinstance(dash, dict):
    cdns = dash.get('cdns', {})
    for cdn_name, cdn_data in cdns.items():
      if isinstance(cdn_data, dict):
        url = cdn_data.get('url', '')
        if url:
          return url
  
  # Fallback: progressive MP4
  progressive = files.get('progressive', [])
  if progressive and isinstance(progressive, list):
    first = progressive[0]
    if isinstance(first, dict):
      return first.get('url', '')
    return str(first)
  
  return ''


def extract_stream_from_iframe(constants: PluginConstants, session: requests.Session, iframe_html: str) -> Tuple[Optional[str], str]:
  """
  Parse the iframe HTML to find config_url, fetch it, extract stream URL.
  """
  # Try direct config_url first
  match = re.search(r'"config_url"\s*:\s*"([^"]+)"', iframe_html)
  if not match:
    # Try OTTData JSON
    match2 = re.search(r'window\.OTTData\s*=\s*({.+?});', iframe_html, re.DOTALL)
    if match2:
      try:
        ott = json.loads(match2.group(1))
        config_url = ott.get('config_url', '')
      except:
        config_url = ''
    else:
      logger.error("No config_url found in iframe HTML")
      logger.debug(f"Iframe HTML (first 2000): {iframe_html[:2000]}")
      return "No config_url in iframe", ""
  else:
    config_url = match.group(1).replace("\\u0026", "&")
  
  if not config_url:
    return "No config_url found", ""
  
  logger.info(f"Config URL: {config_url[:120]}")

  referer = f'https://{constants.url_host_web_app}/'
  r = session.get(config_url, headers={'Referer': referer})
  logResponse(constants, r)
  
  if r.status_code != 200:
    return f"Config request returned {r.status_code}", ""

  try:
    data = r.json()
  except:
    return "Config response is not JSON", ""

  files = data.get('request', {}).get('files', {})
  stream_url = _extract_url_from_files(files)
  
  if not stream_url:
    logger.error(f"No stream URL in config. Files: {json.dumps(files)[:500]}")
    return "No stream URL found in config", ""

  logger.info(f"Stream URL: {stream_url[:120]}")
  return None, stream_url
