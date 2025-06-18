import json

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class AutoNationUSSpider(SitemapSpider, StructuredDataSpider):
    name = "auto_nation_us"
    allowed_domains = ["autonation.com"]
    item_attributes = {"brand": "AutoNation", "brand_wikidata": "Q784804"}
    sitemap_urls = ["https://www.autonation.com/robots.txt"]
    sitemap_rules = [(r"https://www.autonation.com/dealers/[^/]+$", "parse")]
    wanted_types = ["AutoDealer"]
    time_format = "%I:%M %p"
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        store_details = json.loads(response.xpath('//script[@id="store-detail-state"]/text()').get())
        item["lat"] = DictParser.get_nested_key(store_details, "latitude")
        item["lon"] = DictParser.get_nested_key(store_details, "longitude")
        yield item
