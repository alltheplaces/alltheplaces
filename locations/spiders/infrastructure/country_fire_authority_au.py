from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CountryFireAuthorityAUSpider(ArcGISFeatureServerSpider):
    name = "country_fire_authority_au"
    item_attributes = {"operator": "Country Fire Authority", "operator_wikidata": "Q13632973"}
    host = "services-ap1.arcgis.com"
    context_path = "vh59f3ZyAEAhnejO/arcgis"
    service_id = "CFA_Fire_Stations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["site_id"])
        item["name"] = feature["fs_name"]
        item["street_address"] = feature["street"]
        item.pop("street", None)
        item["postcode"] = feature["pcode"]
        apply_category(Categories.FIRE_STATION, item)
        yield item
