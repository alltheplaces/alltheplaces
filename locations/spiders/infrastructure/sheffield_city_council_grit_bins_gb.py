from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

# https://sheffield-city-council-open-data-sheffieldcc.hub.arcgis.com/datasets/9d3d2d8b017749508ecbec2ff704d329_26/explore


class SheffieldCityCouncilGritBinsGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_grit_bins_gb"
    dataset_attributes = (
        ArcGISFeatureServerSpider.dataset_attributes
        | Licenses.GB_OGLv3.value
        | {"attribution:name": "Contains OS data © Crown Copyright [and database right] [year]"}
    )
    item_attributes = {
        "operator": "Sheffield City Council",
        "operator_wikidata": "Q7492609",
        "nsi_id": "N/A",
    }
    host = "sheffieldcitycouncil.cloud.esriuk.com"
    context_path = "server"
    service_id = "AGOL/OpenData"
    layer_id = "26"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.GRIT_BIN, item)
        yield item
