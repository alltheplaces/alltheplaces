from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.urban_planet_ca_pr_us import UrbanPlanetCAPRUSSpider


class CharlotteRusseUSSpider(JSONBlobSpider):
    name = "charlotte_russe_us"
    item_attributes = {"brand": "Charlotte Russe", "brand_wikidata": "Q5086126"}
    allowed_domains = ["charlotterusse.com"]
    start_urls = ["https://charlotterusse.com/apps/api/v1/stores"]
    locations_key = "stores"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        UrbanPlanetCAPRUSSpider.parse_additional_fields(item, feature)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
