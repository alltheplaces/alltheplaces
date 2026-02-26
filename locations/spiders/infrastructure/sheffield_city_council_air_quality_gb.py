from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

# https://sheffield-city-council-open-data-sheffieldcc.hub.arcgis.com/datasets/56a292d1d6de438c954044b2ea063118_1/explore


class SheffieldCityCouncilAirQualityGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_air_quality_gb"
    dataset_attributes = (
        ArcGISFeatureServerSpider.dataset_attributes
        | Licenses.GB_INSPIRE.value
        | {"attribution:name": "SCC Environmental data released under the European Directive INSPIRE."}
    )
    item_attributes = {
        "operator": "Sheffield City Council",
        "operator_wikidata": "Q7492609",
        "nsi_id": "N/A",
    }
    host = "sheffieldcitycouncil.cloud.esriuk.com"
    context_path = "server"
    service_id = "AGOL/INSPIRE"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.MONITORING_STATION, item)
        apply_yes_no(MonitoringTypes.AIR_QUALITY, item, True)
        yield item
