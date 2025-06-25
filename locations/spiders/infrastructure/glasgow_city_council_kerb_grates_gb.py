from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GlasgowCityCouncilKerbGratesGBSpider(ArcGISFeatureServerSpider):
    name = "glasgow_city_council_kerb_grates_gb"
    item_attributes = {
        "operator": "Glasgow City Council",
        "operator_wikidata": "Q130637",
        "nsi_id": "N/A",
    }
    host = "utility.arcgis.com"
    context_path = "usrsvcs/servers/4bce1c0ef79d437586c29fcd03e116bd"
    service_id = "AGOL/Gullies"
    layer_id = "7"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.KERB_GRATE, item)
        yield item
