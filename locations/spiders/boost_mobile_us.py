from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BoostMobileUSSpider(SitemapSpider, StructuredDataSpider):
    name = "boost_mobile_us"
    item_attributes = {
        "brand": "Boost Mobile",
        "brand_wikidata": "Q4943790",
    }
    sitemap_urls = ["https://www.boostmobile.com/locations/sitemap-business-main-pages.xml"]
    sitemap_rules = [(r"/locations/bd/boost-mobile-[a-z]{2}-[-\w]", "parse_sd")]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
        "ROBOTSTXT_OBEY": False,
    }

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data["openingHours"] = ld_data.pop("openingHoursSpecification", [])

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["addr_full"] = item.pop("street_address")
        item["street_address"] = item.pop("name").removeprefix("Boost ")
        yield item
