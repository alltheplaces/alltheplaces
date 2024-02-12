from scrapy.spiders import SitemapSpider

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AutoZoneUSSpider(SitemapSpider, StructuredDataSpider):
    name = "autozone_us"
    item_attributes = {"brand": "AutoZone", "brand_wikidata": "Q4826087"}
    sitemap_urls = ["https://www.autozone.com/locations/sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[a-z]{2}\/[\w\-]+\/[\w\-]+\.html$", "parse_sd")]
    # Playwright is needed to obtain sitemap.xml or else the
    # request is silently blocked and will time out.
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    user_agent = BROWSER_DEFAULT

    def post_process_item(self, item, response, ld_data):
        item["ref"] = item["name"].split(" #", 1)[1]
        item["name"] = item["name"].split(" #", 1)[0]
        item.pop("facebook", None)
        item.pop("twitter", None)
        item.pop("image", None)
        yield item
