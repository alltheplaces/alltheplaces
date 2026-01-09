import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HongkongPostPostboxesHKSpider(ArcGISFeatureServerSpider):
    dataset_attributes = {
        "attribution": "required",
        "attribution:name": "Hongkong Post/Government of Hong Kong via CSDI Portal",
        "attribution:website": "https://portal.csdi.gov.hk/geoportal/?lang=en&datasetId=hkpo_rcd_1638773801007_13653",
        "license": "Terms and Conditions of Use of the CSDI Portal",
        "license:website": "https://portal.csdi.gov.hk/csdi-webpage/doc/TNC",
        "use:commercial": "permit",
    }
    name = "hongkong_post_postboxes_hk"
    item_attributes = {"operator": "香港郵政 Hongkong Post", "operator_wikidata": "Q196631"}
    host = "portal.csdi.gov.hk"
    context_path = "server"
    service_id = "common/hkpo_rcd_1638773801007_13653"
    layer_id = "0"
    postbox_ref_regex = re.compile(r"(?:(?:^street posting box)(?:es)? no.? ?)(.*$)")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.POST_BOX, item)
        ref = self.postbox_ref_regex.match(feature["NAME_EN"].lower)
        if ref is None:
            self.logger.warning("Ref not found for postbox: {}".format(feature["NAME_EN"]))
        else:
            item["ref"] = ref.group(1)
        # to add: collection times
        yield item
