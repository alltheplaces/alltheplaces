import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser


class WilliamHillGBSpider(CrawlSpider):
    name = "william_hill_gb"
    item_attributes = {"brand": "William Hill", "brand_wikidata": "Q4053147"}
    allowed_domains = ["shoplocator.williamhill"]
    start_urls = ["https://shoplocator.williamhill/directory"]
    rules = [Rule(LinkExtractor(), callback="parse_func", follow=False)]

    def parse_func(self, response):
        pattern = re.compile(r"window.lctr.results.push\((.*?)\);", re.MULTILINE | re.DOTALL)
        if s := response.xpath('//script[contains(., "lctr")]/text()').re(pattern):
            store = json.loads(s[0])
            item = DictParser.parse(store)
            item["website"] = response.url
            components = list(filter(None, [store.get("street_no"), store.get("street")]))
            item["street_address"] = " ".join(map(str.strip, components)).strip()
            item["city"] = store.get("county")
            return item
