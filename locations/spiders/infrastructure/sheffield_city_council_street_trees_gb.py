from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

# https://sheffield-city-council-open-data-sheffieldcc.hub.arcgis.com/datasets/7b2df397e9994ca5984bad0b679ce6d9_14/explore


class SheffieldCityCouncilStreetTreesGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_street_trees_gb"
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
    layer_id = "14"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["id"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature.get("featuretypename")
        yield item
