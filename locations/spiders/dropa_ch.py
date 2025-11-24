from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DropaCHSpider(CrawlSpider, StructuredDataSpider):
    name = "dropa_ch"
    item_attributes = {"brand": "Dropa", "brand_wikidata": "Q1260273"}
    start_urls = ["https://dropa.ch/standorte"]
    rules = [Rule(LinkExtractor("/standorte/dropa-"), "parse")]
    wanted_types = ["Pharmacy"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("DROPA ").replace("Apotheke", "").replace("Drogerie", "")
        item["image"] = None
        extract_google_position(item, response)
        yield item
