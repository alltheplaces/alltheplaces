from copy import deepcopy

from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class StateFarmUSSpider(SitemapSpider, StructuredDataSpider):
    name = "state_farm_us"
    item_attributes = {"brand": "State Farm", "brand_wikidata": "Q2007336", "country": "US"}
    sitemap_urls = ["https://www.statefarm.com/sitemap-agents.xml"]
    sitemap_rules = [(r"/agent/us/\w\w/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["WebSite"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
        "DEFAULT_REQUEST_HEADERS": {
            "User-Agent": BROWSER_DEFAULT,
        },
    }

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        mainEntity = ld_data.get("mainEntity")
        for office in mainEntity.get("geo", []):
            # It can be more than one office for a single agent
            item = deepcopy(item)
            item["ref"] = item["ref"] + "-" + office.get("address", {}).get("postalCode")
            item["lat"] = office.get("latitude")
            item["lon"] = office.get("longitude")
            item["city"] = office.get("address", {}).get("addressLocality")
            item["state"] = office.get("address", {}).get("addressRegion")
            item["postcode"] = office.get("address", {}).get("postalCode")
            item["street_address"] = office.get("address", {}).get("streetAddress")
            yield item
