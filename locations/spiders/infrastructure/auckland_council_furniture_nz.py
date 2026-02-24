from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AucklandCouncilFurnitureNZ(ArcGISFeatureServerSpider):
    name = "auckland_council_furniture_nz"
    item_attributes = {"operator": "Auckland Council", "operator_wikidata": "Q758635"}
    host = "services1.arcgis.com"
    context_path = "n4yPwebTjJCmXB6W/ArcGIS"
    service_id = "Park_Fixture_Furniture"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["SAPID"]

        if furniture_type := feature.get("AssetGroup"):
            match furniture_type:
                case "BBQ":
                    apply_category(Categories.BARBECUE, item)
                case "Bike Stand":
                    apply_category(Categories.BICYCLE_PARKING, item)
                case "Drinking Fountain":
                    apply_category({"amenity": "drinking_water", "fountain": "drinking"}, item)
                case "Fitness Station":
                    apply_category(Categories.LEISURE_FITNESS_STATION, item)
                case "Rubbish Bin":
                    apply_category(Categories.WASTE_BASKET, item)
                case "Seat":
                    apply_category(Categories.BENCH, item)
                case "Shower" | "Beach Shower":
                    apply_category({"amenity": "shower"}, item)
                case "Table":
                    apply_category(Categories.LEISURE_PICNIC_TABLE, item)
                case _:
                    self.logger.warning("Unknown furniture type: {}".format(furniture_type))

        yield item
