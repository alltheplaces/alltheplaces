from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import apply_category, Categories
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from scrapy.linkextractors import LinkExtractor


class BricoramaFRSpider(CrawlSpider, StructuredDataSpider):
    name = "bricorama_fr"
    item_attributes = {"brand": "Bricorama", "brand_wikidata": "Q2925146"}
    start_urls = ["https://www.bricorama.fr/magasins?device=mobile"]
    rules = [Rule(LinkExtractor(r"/magasin/[^/]+/(\d+)$"), "parse")]
    wanted_types = ["HomeAndConstructionBusiness"]

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data["openingHoursSpecification"] = None  # Malformed and out of sync with HTML

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Bricorama ")
        if postcode := item.get("postcode"):
            item["postcode"] = str(postcode)
        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item
