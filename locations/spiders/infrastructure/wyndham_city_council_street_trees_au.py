from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WyndhamCityCouncilStreetTreesAUSpider(JSONBlobSpider):
    name = "wyndham_city_council_street_trees_au"
    item_attributes = {"brand": "Wyndham City Council", "brand_wikidata": "Q96773743", "state": "VIC"}
    allowed_domains = ["digital.wyndham.vic.gov.au"]
    start_urls = [
        "https://digital.wyndham.vic.gov.au/treeplanting-season/getGeoJson/-37.72700873131489,-38.02023822658594,143.70666503906253,145.05249023437503"
    ]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        item["addr_full"] = feature["property_address"]
        if status := feature["status"]:
            match status.lower().removesuffix("2023").strip():
                case "pending" | "proposedsite" | "vandalised":
                    return
                case "alive" | "dead" | "notsuitable" | "planted" | "suitable" | "unchecked":
                    pass
                case _:
                    self.logger.warning("Unknown tree status: {}".format(status))
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature["current_botanical_name"]
        item["extras"]["taxon:en"] = feature["current_common_name"]
        yield item
