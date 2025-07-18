from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.urban_planet_ca_pr_us import UrbanPlanetCAPRUSSpider


class BluenotesCASpider(JSONBlobSpider):
    name = "bluenotes_ca"
    allowed_domains = ["blnts.com"]
    start_urls = ["https://blnts.com/apps/api/v1/stores"]
    locations_key = "stores"
    brands = {
        "Aeropostale": {"brand": "Aeropostale", "brand_wikidata": "Q794565"},
        "Bluenotes": {"brand": "Bluenotes", "brand_wikidata": "Q4930395"},
        "Thriftys by Bluenotes": {"brand": "Thrifty's", "brand_wikidata": "Q135390727"},
    }
    # For Aéropostale stores in the USA, see spider `aeropostale_us`.

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        brand_name = feature["brand"].strip()
        if brand_name not in self.brands.keys():
            self.logger.warning(
                "Unknown brand '{}'. Feature extracted without brand_wikidata set. Spider needs updating to map the brand to a Wikidata item.".format(
                    brand_name
                )
            )
            item["brand"] = brand_name
        else:
            item["brand"] = self.brands[brand_name]["brand"]
            item["brand_wikidata"] = self.brands[brand_name]["brand_wikidata"]
        UrbanPlanetCAPRUSSpider.parse_additional_fields(item, feature)
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
