import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PrimeraNLSpider(CrawlSpider, StructuredDataSpider):
    name = "primera_nl"
    item_attributes = {"brand": "Primera", "brand_wikidata": "Q2176149"}
    start_urls = ["https://www.primera.nl/winkels"]
    rules = [
        Rule(
            LinkExtractor(allow=r"https://www\.primera\.nl/primera-"),
            callback="parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        opening_hours = ld_data.get("openingHoursSpecification", [])
        if all(not rule.get("opens") for rule in opening_hours):
            return
        if match := re.search(r"lat:(-?\d+\.\d+),lng:(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = match.groups()
        item["branch"] = item.pop("name").replace("Primera ", "")
        yield item
