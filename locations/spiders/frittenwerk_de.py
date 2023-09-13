import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class FrittenwerkDESpider(CrawlSpider, StructuredDataSpider):
    name = "frittenwerk_de"
    item_attributes = {"brand": "Frittenwerk", "brand_wikidata": "Q121094275"}
    start_urls = ["https://frittenwerk.com/index.php"]
    rules = [Rule(LinkExtractor(restrict_xpaths='//li[@class="locchange "]'), callback="parse")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if lat := re.search(r'"latitude": "(-?\d+\.\d+)"', response.text):
            item["lat"] = lat.group(1)

        if lon := re.search(r'"longitude": "(-?\d+\.\d+)"', response.text):
            item["lon"] = lon.group(1)

        item["extras"]["branch"] = item.pop("name").replace("Frittenwerk ", "")

        yield item
