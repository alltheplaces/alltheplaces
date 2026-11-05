from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BoostMobileUSSpider(SitemapSpider, StructuredDataSpider):
    name = "boost_mobile_us"
    item_attributes = {
        "brand": "Boost Mobile",
        "brand_wikidata": "Q4943790",
    }
    sitemap_urls = ["https://www.boostmobile.com/locations/sitemap.xml"]
    sitemap_rules = [(r"/locations/bd/boost-mobile-[a-z]{2}-[-\w]", "parse_sd")]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
    }

    def pre_process_data(self, ld_data: dict, **kwargs):
        if opening_hours_specification := ld_data.pop("openingHoursSpecification", None):
            ld_data["openingHours"] = opening_hours_specification

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item.pop("name")
        item["image"] = None
        if "Temporarily Closed" in response.xpath('//*[contains(@class, "location-details")]').get(""):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].set_closed(DAYS)
        yield item
