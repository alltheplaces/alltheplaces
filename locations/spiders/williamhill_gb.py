import json
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from locations.dict_parser import DictParser


class WilliamHillGBSpider(CrawlSpider):
    name = "williamhill_gb"
    item_attributes = {
        "brand": "William Hill",
        "brand_wikidata": "Q4053147",
        "country": "GB",
    }
    allowed_domains = ["shoplocator.williamhill"]
    start_urls = ["https://shoplocator.williamhill/directory"]
    rules = [Rule(LinkExtractor(), callback="parse_func", follow=False)]
    download_delay = 0.5

    def parse_func(self, response):
        pattern = re.compile(
            r"window.lctr.results.push\((.*?)\);", re.MULTILINE | re.DOTALL
        )
        s = response.xpath('//script[contains(., "lctr")]/text()').re(pattern)
        if s:
            store = json.loads(s[0])
            item = DictParser.parse(store)
            item["website"] = response.url
            street_no = store.get("street_no", "").strip()
            street = store.get("street", "").strip()
            item["street_address"] = (street_no + " " + street).strip()
            item["city"] = store.get("county")
            return item
