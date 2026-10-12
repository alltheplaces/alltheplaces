from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CanadaPostStreetLetterBoxesCASpider(ArcGISFeatureServerSpider):
    name = "canada_post_street_letter_boxes_ca"
    item_attributes = {"operator": "Canada Post", "operator_wikidata": "Q1032001"}
    # Same public map server as canada_post_ca. Only street letter boxes (SLB) in service: the layer also
    # holds community mailboxes and kiosks, which are delivery boxes, not places to post letters.
    host = "pub.geo.canadapost-postescanada.ca"
    context_path = "server"
    service_id = "Hosted/STREET_FURNITURE"
    layer_id = "0"
    where_query = "assettypeen = 'SLB' AND lifecyclestatusen = 'ACTV'"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("assetidentifier") or feature.get("globalid")
        item.pop("name", None)
        item["housenumber"] = feature.get("streetnumber")
        item["street"] = feature.get("streetname")
        item["state"] = feature.get("province")
        if description := feature.get("locationdescriptionen"):
            item["extras"]["description"] = description
        apply_category(Categories.POST_BOX, item)
        yield item
