from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HastingsDistrictCouncilWasteBasketsNZSpider(ArcGISFeatureServerSpider):
    name = "hastings_district_council_waste_baskets_nz"
    item_attributes = {"operator": "Hastings District Council", "operator_wikidata": "Q73811101"}
    host = "gismaps.hdc.govt.nz"
    context_path = "server"
    service_id = "ParksReserves/Parks_and_Reserves"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["system_id"])
        apply_category(Categories.WASTE_BASKET, item)
        match feature["bin_type"]:
            case "Doggy Doos Bin":
                item["extras"]["waste"] = "dog_excrement"
            case "Recycle Bin":
                item["extras"]["waste"] = "recycling"
            case "Rubbish Bin":
                item["extras"]["waste"] = "trash"
            case None:
                pass
            case _:
                self.logger.warning("Unknown bin type: {}".format(feature["bin_type"]))
        match feature["material"]:
            case "Aluminum":
                item["extras"]["material"] = "aluminium"
            case "Plastic" | "PVC":
                item["extras"]["material"] = "plastic"
            case "Stainless Steel" | "Steel":
                item["extras"]["material"] = "steel"
            case "Steel Corten":
                item["extras"]["material"] = "weathering_steel"
            case "Steel/Aluminum":
                item["extras"]["material"] = "aluminium;steel"
            case "Steel/Timber" | "Timber/Steel":
                item["extras"]["material"] = "steel;wood"
            case "Timber":
                item["extras"]["material"] = "wood"
            case "UNKNOWN" | None:
                pass
            case _:
                self.logger.warning("Unknown bin material: {}".format(feature["material"]))
        yield item
