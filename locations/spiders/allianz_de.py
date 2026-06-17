from scrapy.spiders import SitemapSpider

from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AllianzDESpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "allianz_de"
    item_attributes = {"brand": "Allianz", "brand_wikidata": "Q487292"}
    sitemap_urls = [
        "https://vertretung.allianz.de/sitemap.xml",
    ]
    sitemap_rules = [("", "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, response, ld_data):
        item["phone"] = ld_data.get("telePhone", None)
        yield item
