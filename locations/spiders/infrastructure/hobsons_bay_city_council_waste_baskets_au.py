from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HobsonsBayCityCouncilWasteBasketsAUSpider(ArcGISFeatureServerSpider):
    name = "hobsons_bay_city_council_waste_baskets_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    host = "services3.arcgis.com"
    context_path = "gToGKwidNkZbWBGJ/ArcGIS"
    service_id = "Litter%20Bins_point"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["central_as"]
        apply_category(Categories.WASTE_BASKET, item)

        if feature["BinSize"] and feature["BinSize"].endswith(" Litres"):
            # "volume" is a made-up key that doesn't currently exist in OSM.
            # No other existing key for the volume of a bin appears to
            # currently exist in OSM.
            item["extras"]["volume"] = feature["BinSize"].lower()

        match feature["LitterBinM"]:
            case "Plastic":
                item["extras"]["material"] = "plastic"
            case "Stainless" | "Stainless/Steel" | "Steel":
                item["extras"]["material"] = "steel"
            case "Steel/Plastic":
                item["extras"]["material"] = "plastic;steel"
            case "Steel/Timber/Plastic":
                item["extras"]["material"] = "plastic;steel;wood"
            case "Not Applicable":
                pass
            case _:
                raise ValueError("Unknown waste basket material type: {}".format(feature["LitterBinM"]))

        yield item
