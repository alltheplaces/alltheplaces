from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

# https://sheffield-city-council-open-data-sheffieldcc.hub.arcgis.com/datasets/7fadfc65232a4af1838616ec81c7aeae_12/explore


class SheffieldCityCouncilBenchesGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_benches_gb"
    dataset_attributes = ArcGISFeatureServerSpider.dataset_attributes | Licenses.GB_OGLv3.value
    item_attributes = {
        "operator": "Sheffield City Council",
        "operator_wikidata": "Q7492609",
        "nsi_id": "N/A",
    }
    host = "sheffieldcitycouncil.cloud.esriuk.com"
    context_path = "server"
    service_id = "AGOL/OpenData1"
    layer_id = "12"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.BENCH, item)
        yield item
