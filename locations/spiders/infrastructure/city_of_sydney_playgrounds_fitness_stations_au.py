from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfSydneyPlaygroundsFitnessStationsAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_sydney_playgrounds_fitness_stations_au"
    item_attributes = {"operator": "City of Sydney", "operator_wikidata": "Q56477532", "state": "NSW"}
    host = "services1.arcgis.com"
    context_path = "cNVyNtjGVZybOQWZ/ArcGIS"
    service_id = "Playgrounds"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        if feature["Type"] == "Playground":
            apply_category(Categories.LEISURE_PLAYGROUND, item)
        elif feature["Type"] == "Fitness station":
            apply_category(Categories.LEISURE_FITNESS_STATION, item)
        else:
            raise RuntimeError("Unknown type of feature cannot be extracted: {}".format(feature["Type"]))
        yield item
