import json
import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class NewYorkPublicLibraryUSSpider(CrawlSpider):
    name = "new_york_public_library_us"
    item_attributes = {"operator": "New York Public Library", "operator_wikidata": "Q219555"}

    start_urls = [
        "https://www.nypl.org/locations",
    ]
    rules = [Rule(LinkExtractor(r"/locations/[^/]+$"), "parse")]

    def parse(self, response):
        address_data = DictParser.get_nested_key(
            json.loads(response.xpath('//*[@id="__NEXT_DATA__"]//text()').get()), "secondaryContent"
        )
        item = DictParser.parse(address_data)
        item["branch"] = response.xpath("//h1//text()").get()
        item["ref"] = item["website"] = response.url
        apply_category(Categories.LIBRARY, item)
        if lat_lon := re.search(r"\"lat\":\s*(\d+\.\d+),\s*\"lng\":\s*(-?\d+\.\d+)", response.text):
            item["lat"] = lat_lon.groups()[0]
            item["lon"] = lat_lon.groups()[1]
        yield item
