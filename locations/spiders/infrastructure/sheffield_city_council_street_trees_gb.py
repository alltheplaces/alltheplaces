from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SheffieldCityCouncilStreetTreesGBSpider(ArcGISFeatureServerSpider):
    name = "sheffield_city_council_street_trees_gb"
    dataset_attributes = {
        "source": "api",
        "api": "arcgis",
        "license": "INSPIRE End User Licence",
        "license:website": "https://www.ordnancesurvey.co.uk/documents/licensing/inspire-end-user-licence.pdf",
    }
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
