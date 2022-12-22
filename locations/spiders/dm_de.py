import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.structured_data_spider import StructuredDataSpider


class DrogerieMarktSpider(SitemapSpider):
    name = "dm_de"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    sitemap_urls = ["https://store-data-service.services.dmtech.com/sitemap/DE"]
    sitemap_rules = [(r"www.dm.de/store/", "parse")]
    download_delay = 0.5

    def sitemap_filter(self, entries):
        # Convert the sitemap entry into a query to the JSON API
        for entry in entries:
            if m := re.search(r"store/de-([0-9]+)/", entry["loc"]):
                entry["loc"] = f"https://store-data-service.services.dmtech.com/stores/item/de/{m.group(1)}"
                yield entry

    def parse(self, response):
        entry = DictParser.parse(response.json())
        yield entry
