from datetime import UTC, datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class TennetTowersNLSpider(ArcGISFeatureServerSpider):
    name = "tennet_towers_nl"
    item_attributes = {"operator": "TenneT TSO", "operator_wikidata": "Q113465523"}
    host = "services-eu1.arcgis.com"
    context_path = "WjozPuR5ROn6NZE8/ArcGIS"
    service_id = "TenneT_Assets_Hoogspanning"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["SE_FLD20_OBJECTID"]
        apply_category(Categories.POWER_TOWER, item)
        item["extras"]["alt_ref"] = feature["SE_FLD18_MASTNUMMER"]
        if construction_date_int := feature.get("SE_FLD4_BOUWJAAR"):
            construction_date = datetime.fromtimestamp(int(float(construction_date_int) / 1000), UTC)
            item["extras"]["start_date"] = construction_date.isoformat().split("T", 1)[0]
        yield item
