from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ShurgardSpider(CrawlSpider, StructuredDataSpider):
    name = "shurgard"
    item_attributes = {"brand": "Shurgard", "brand_wikidata": "Q3482670"}

    start_urls = [
        "https://www.shurgard.com/nl-be/opslagruimte-huren",
        "https://www.shurgard.com/da-dk/opbevaringsrum",
        "https://www.shurgard.com/fr-fr/garde-meuble",
        "https://www.shurgard.com/de-de/lagerraum-mieten",
        "https://www.shurgard.com/nl-nl/opslagruimte-in-nederland",
        "https://www.shurgard.com/sv-se/hyra-forrad",
        "https://www.shurgard.com/en-gb/self-storage-uk",
    ]

    # Store pages sit below city pages, which only carry a summary of their stores
    rules = [
        Rule(LinkExtractor(r"/opslagruimte-huren/[^/]+/[^/]+"), callback="parse_sd"),
        Rule(LinkExtractor(r"/opbevaringsrum/[^/]+/[^/]+"), callback="parse_sd"),
        Rule(LinkExtractor(r"/garde-meuble/[^/]+/[^/]+"), callback="parse_sd"),
        Rule(LinkExtractor(r"/lagerraum-mieten/[^/]+/[^/]+"), callback="parse_sd"),
        Rule(LinkExtractor(r"/opslagruimte-in-nederland/[^/]+/[^/]+"), callback="parse_sd"),
        Rule(LinkExtractor(r"-forrad/[^/]+/[^/]+"), callback="parse_sd"),
        Rule(LinkExtractor(r"/self-storage-uk/[^/]+/[^/]+"), callback="parse_sd"),
    ]
    time_format = "%I:%M %p"

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data["openingHoursSpecification"] = [
            rule for rule in ld_data.get("openingHoursSpecification") or [] if rule.get("name") == "Office hours"
        ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
