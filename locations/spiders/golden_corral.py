from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.linked_data_parser import LinkedDataParser


class GoldenCorralSpider(CrawlSpider):
    name = "golden_corral"
    item_attributes = {"brand": "Golden Corral", "brand_wikidata": "Q4039560"}
    allowed_domains = ["goldencorral.com"]
    start_urls = ["https://www.goldencorral.com/locations/all-locations"]
    rules = [Rule(LinkExtractor(allow="/location-detail/"), callback="parse", follow=False)]
    drop_attributes = {"image"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if item := LinkedDataParser.parse(response, "Restaurant"):
            item["country"] = "US"
            item["ref"] = response.url
            yield item
