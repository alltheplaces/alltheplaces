from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.kate_spade import KateSpadeSpider
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class KateSpadeCAUSSpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "kate_spade_ca_us"
    item_attributes = KateSpadeSpider.item_attributes
    sitemap_urls = ["https://www.katespade.com/stores/sitemap.xml"]
    sitemap_rules = [(r"/stores/\w\w/[-\w]+/[-\w]+$", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT} | DEFAULT_PLAYWRIGHT_SETTINGS
    drop_attributes = {"facebook"}

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("About ")
        yield item
