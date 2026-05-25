from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class GlenEiraCityCouncilDrainManholesAUSpider(JSONBlobSpider):
    name = "glen_eira_city_council_drain_manholes_au"
    item_attributes = {"operator": "Glen Eira City Council", "operator_wikidata": "Q56477767", "state": "VIC"}
    allowed_domains = ["connect.pozi.com"]
    start_urls = ["https://connect.pozi.com/userdata/gleneira-publisher/Council-Facilities-and-Services/Pit.json"]
    locations_key = "features"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,  # Avoid HTTP 403 error
    }

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("properties"))

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["feature_id"]
        item["addr_full"] = feature["feature_location"]
        apply_category(Categories.MANHOLE, item)
        item["extras"]["alt_ref"] = feature["central_asset_id"]
        item["extras"]["manhole"] = "drain"
        item["extras"]["utility"] = "stormwater"
        item["extras"]["substance"] = "rainwater"
        if material := feature.get("d-material"):
            material = material.strip()
            match material:
                case "Bluestone":
                    item["extras"]["material"] = "bluestone"
                case "Brick":
                    item["extras"]["material"] = "brick"
                case "Concrete":
                    item["extras"]["material"] = "concrete"
                case "Not Applicable" | "Other":
                    pass
                case _:
                    self.logger.warning("Unknown material type: {}".format(material))
        yield item
