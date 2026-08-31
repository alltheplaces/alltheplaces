from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.opendatasoft_explore import OpendatasoftExploreSpider


class NorthernPowergridLvSupportsGBSpider(OpendatasoftExploreSpider):
    name = "northern_powergrid_lv_supports_gb"
    item_attributes = {"operator": "Northern Powergrid", "operator_wikidata": "Q7058871"}
    dataset_attributes = OpendatasoftExploreSpider.dataset_attributes | {
        "license": "Northern Powergrid Open Data Licence v1.0",
        "license:website": "https://northernpowergrid.opendatasoft.com/p/opendatalicence/",
        "attribution": "required",
        "attribution:name": "Supported by Northern Powergrid Open Data",
    }
    api_endpoint = "https://northernpowergrid.opendatasoft.com/api/explore/v2.1/"
    dataset_id = "lv-support-locations"
    no_refs = True

    SUPPORT_TYPE_MAP = {
        "WOOD POLE - SINGLE": {"material": "wood"},
        "WOOD POLE - H": {"material": "wood", "design": "h-frame"},
        "WOOD POLE - SHORT H": {"material": "wood", "design": "h-frame"},
        "WOOD POLE - A": {"material": "wood"},
        "STEEL POLE": {"material": "steel"},
        "CONCRETE POLE": {"material": "concrete"},
    }

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        support_type = feature.get("support_type")

        # Wall-mounted cables
        if support_type == "BRACKET / ATTACHMENT":
            return

        if extras := self.SUPPORT_TYPE_MAP.get(support_type):
            item["extras"].update(extras)

        if height := feature.get("support_height_meters"):
            item["extras"]["height"] = str(int(height))

        apply_category(Categories.POWER_POLE, item)
        yield item
