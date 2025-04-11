from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class NapaSpider(CrawlSpider, StructuredDataSpider):
    name = "napa"
    item_attributes = {"brand": "NAPA Auto Parts", "brand_wikidata": "Q6970842"}
    download_delay = 2
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 90 * 1000}
    start_urls = ["https://www.napaonline.com/en/auto-parts-stores-near-me"]
    rules = [
        Rule(LinkExtractor(allow=r"/en/auto-parts-stores-near-me/[a-z]{2}$")),
        Rule(LinkExtractor(allow=r"/en/auto-parts-stores-near-me/[a-z]{2}/[-\w]+$"), callback="parse_sd"),
        Rule(LinkExtractor(allow=r"/en/[a-z]{2}/[-\w]+/store/\d+"), callback="parse_sd"),
    ]
    time_format = "%H:%M:%S"

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_CAR_PARTS, item)
        yield item
