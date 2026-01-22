from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class VintageInnsGBSpider(JSONBlobSpider):
    name = "vintage_inns_gb"
    item_attributes = {"brand": "Vintage Inns", "brand_wikidata": "Q87067899"}
    start_urls = ["https://www.vintageinn.co.uk/cborms/pub/brands/8/outlets/"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True
