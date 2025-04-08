from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfPerthTreesAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_perth_trees_au"
    item_attributes = {"operator": "City of Perth", "operator_wikidata": "Q56477938", "state": "WA"}
    host = "services7.arcgis.com"
    context_path = "v8XBa2naYNQGOjlG/ArcGIS"
    service_id = "PKS_AST_TREESMASTER_PV"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["TREE_ID"])
        item["city"] = feature["SUBURB"]
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature.get("BOTANICAL_NAME")
        item["extras"]["taxon:en"] = feature.get("COMMON_NAME")
        if height_m := feature.get("TREE_HEIGHT"):
            item["extras"]["height"] = f"{height_m} m"
        if planted_unix_timestamp := feature.get("DATE_PLANTED"):
            if planted_unix_timestamp != -2208988800000:
                # Ignore dates which are Unix epoch (1 Jan 1970 00:00:00) as
                # these are unknown/unspecified planting dates.
                planted_date = datetime.fromtimestamp(int(float(planted_unix_timestamp) / 1000), UTC)
                item["extras"]["start_date"] = planted_date.strftime("%Y-%m-%d")
        yield item
