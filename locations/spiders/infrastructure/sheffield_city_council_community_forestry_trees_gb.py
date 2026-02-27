from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider

# https://sheffield-city-council-open-data-sheffieldcc.hub.arcgis.com/datasets/47dbf190bd254de8aea2008e6aedbbd2_14/explore


class SheffieldCityCouncilCommunityForestryTreesGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_community_forestry_trees_gb"
    dataset_attributes = ArcGISFeatureServerSpider.dataset_attributes | Licenses.GB_OGLv3.value
    item_attributes = {
        "operator": "Sheffield City Council",
        "operator_wikidata": "Q7492609",
        "nsi_id": "N/A",
    }
    host = "sheffieldcitycouncil.cloud.esriuk.com"
    context_path = "server"
    service_id = "AGOL/Community_Forestry_Trees"
    layer_id = "14"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["treeid"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["species"] = feature.get("species")
        yield item
