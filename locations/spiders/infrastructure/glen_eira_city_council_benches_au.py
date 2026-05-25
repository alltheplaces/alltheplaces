import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlenEiraCityCouncilBenchesAUSpider(JSONBlobSpider):
    name = "glen_eira_city_council_benches_au"
    item_attributes = {"operator": "Glen Eira City Council", "operator_wikidata": "Q56477767", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/gleneira-publisher/Council-Facilities-and-Services/Public_Seating.json"]
    locations_key = "features"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # Avoid HTTP 403 error
    }

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if feature.get("feature_id"):
            if feature_id := re.search(r"^(PF\d+)$", feature["feature_id"]):
                item["ref"] = feature_id.group(1)
            else:
                item["ref"] = str(feature["ogr_fid"])
        else:
            item["ref"] = str(feature["ogr_fid"])
        apply_category(Categories.BENCH, item)
        match feature.get("Material"):
            case "Aluminium":
                item["extras"]["material"] = "aluminium"
            case "Bluestone":
                item["extras"]["material"] = "bluestone"
            case "Brick":
                item["extras"]["material"] = "brick"
            case "Concrete":
                item["extras"]["material"] = "concrete"
            case "Plastic":
                item["extras"]["material"] = "plastic"
            case "Steel" | "Stainless Steel":
                item["extras"]["material"] = "steel"
            case "Timber":
                item["extras"]["material"] = "wood"
            case "Timber/Concrete" | "Concrete/Steel":
                item["extras"]["material"] = "concrete;wood"
            case "Timber/Steel":
                item["extras"]["material"] = "steel;wood"
            case "Not Applicable" | "Other" | None:
                pass
            case _:
                self.logger.warning("Unknown material type: {}".format(feature["Material"]))
        yield item
