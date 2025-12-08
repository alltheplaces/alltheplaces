from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class WesternPowerSubstationsAUSpider(ArcGISFeatureServerSpider):
    name = "western_power_substations_au"
    item_attributes = {"operator": "Western Power", "operator_wikidata": "Q7988180"}
    host = "services2.arcgis.com"
    context_path = "tBLxde4cxSlNUxsM/ArcGIS"
    service_id = "NCMT_Data_2024_gdb"
    layer_id = "7"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("OWNER") != "WP":
            # Privately owned substation (typically at a factory or mine).
            return
        item["ref"] = feature["SUB_ABBRV"]
        item["state"] = "WA"
        if feature.get("DESCRIP") == "Current Western Power Terminal/Power Station":
            apply_category(Categories.SUBSTATION_TRANSMISSION, item)
        elif feature.get("DESCRIP") == "Existing Western Power Substation":
            apply_category(Categories.SUBSTATION_ZONE, item)
        else:
            self.logger.warning("Unknown substation/asset type: {}".format(feature.get("DESCRIP")))
            return
        yield item
