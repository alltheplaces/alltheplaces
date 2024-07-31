import html
import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser


class ScrewfixGBSpider(CrawlSpider):
    name = "screwfix_gb"
    item_attributes = {"brand": "Screwfix", "brand_wikidata": "Q7439115"}
    allowed_domains = ["www.screwfix.com"]
    start_urls = ["https://www.screwfix.com/stores/all"]
    rules = [Rule(LinkExtractor(allow=r"\/stores\/([A-Z][A-Z][0-9])\/.+$"), callback="parse")]
    wanted_types = ["HardwareStore"]

    def parse(self, response):
        data = response.xpath('//script[@type="application/ld+json"][contains(., "HardwareStore")]/text()').get()
        if not data:
            return

        data = html.unescape(data)
        data_json = json.loads(data)
        if not data_json:
            return

        item = LinkedDataParser.parse_ld(data_json)
        item["website"] = response.url

        if "phone" in item and item["phone"] is not None and item["phone"].replace(" ", "").startswith("+443"):
            item.pop("phone", None)

        item.pop("name", None)

        yield item
