from typing import Iterable

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FlannelsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "flannels_gb"
    item_attributes = {"brand": "Flannels", "brand_wikidata": "Q18160381"}
    start_urls = ["https://www.flannels.com/stores/az"]
    rules = [Rule(LinkExtractor(allow="/stores/"), "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data.pop("sameAs")
        return ld_data

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Flannels ", "")
        yield item
