class PluginConstants():
  """
  Plugin Constants
  """
  def __init__(
      self,
      base_url: str,
      addon_handle: int,
      query: str,
      site_id: int,
      hub_id: int,
      url_host_web_app: str,
      url_api_featured: str,
      url_api_collections: str
    ):
    self.base_url = base_url
    self.addon_handle = addon_handle
    self.query = query
    self.site_id = site_id
    self.hub_id = hub_id
    self.url_host_web_app = url_host_web_app
    self.url_api_featured = url_api_featured
    self.url_api_collections = url_api_collections
