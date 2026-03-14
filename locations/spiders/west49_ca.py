from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.urban_planet_ca_pr_us import UrbanPlanetCAPRUSSpider


class West49CASpider(JSONBlobSpider):
    name = "west49_ca"
    item_attributes = {"brand": "West 49", "brand_wikidata": "Q7984218"}
    allowed_domains = ["west49.com"]
    start_urls = ["https://west49.com/apps/api/v1/stores"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        UrbanPlanetCAPRUSSpider.parse_additional_fields(item, feature)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
