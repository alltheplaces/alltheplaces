from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.urban_planet_ca_pr_us import UrbanPlanetCAPRUSSpider


class SuzyShierCASpider(JSONBlobSpider):
    name = "suzy_shier_ca"
    item_attributes = {"brand": "Suzy Shier", "brand_wikidata": "Q65464976"}
    allowed_domains = ["suzyshier.com"]
    start_urls = ["https://suzyshier.com/apps/api/v1/stores"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        UrbanPlanetCAPRUSSpider.parse_additional_fields(item, feature)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
