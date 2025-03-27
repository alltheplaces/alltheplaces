from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CambridgeCityCouncilGritBinsUSSpider(ArcGISFeatureServerSpider):
    name = "cambridge_city_council_grit_bins_us"
    item_attributes = {"operator": "Cambridge City Council", "operator_wikidata": "Q133054988", "state": "MA"}
    host = "services1.arcgis.com"
    context_path = "WnzC35krSYGuYov4/ArcGIS"
    service_id = "Salt_Barrels"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["Label"])
        item["name"] = feature["Location"]
        item["street_address"] = feature["Street"]
        item.pop("street", None)
        apply_category(Categories.GRIT_BIN, item)
        yield item
