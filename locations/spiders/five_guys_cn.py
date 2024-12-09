import re
from urllib import parse

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.spiders.five_guys_us import FIVE_GUYS_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysCNSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_cn"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    sitemap_urls = ["https://restaurants.fiveguys.cn/sitemap.xml"]
    sitemap_rules = [(r"https://restaurants.fiveguys.cn/en_cn/[-\w&]+$", "parse_sd")]
    wanted_types = ["FastFoodRestaurant"]  # Explicitly mention the type to ignore duplicate linked data

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if match := re.search(r"yextDisplay.+?,", response.text):
            coordinates = chompjs.parse_js_object(parse.unquote(match.group(0)))
            item["lat"] = coordinates["latitude"]
            item["lon"] = coordinates["longitude"]
        yield item
