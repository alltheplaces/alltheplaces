from copy import deepcopy
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiBWLSNASZZASpider(JSONBlobSpider):
    name = "hyundai_bw_ls_na_sz_za"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["api.hyundai.co.za"]
    start_urls = ["https://api.hyundai.co.za/api/Dealers"]
    needs_json_request = True
    skip_auto_cc_domain = True

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature.get("Description")

        if hours := feature.get("OperatingHours"):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)

        if slug := feature.get("Slug"):
            item["website"] = "https://www.hyundai.co.za/dealers/" + slug

        if feature.get("Sales") or feature.get("CommercialSales"):
            shop = deepcopy(item)
            apply_category(Categories.SHOP_CAR, shop)
            if feature.get("Service") or feature.get("CommercialService"):
                apply_yes_no(Extras.CAR_REPAIR, shop, True)
            if feature.get("Parts") or feature.get("CommercialParts"):
                apply_yes_no(Extras.CAR_PARTS, shop, True)
            yield shop

        if feature.get("Service") or feature.get("CommercialService"):
            service = deepcopy(item)
            service["ref"] = f"{item['ref']}_service"
            apply_category(Categories.SHOP_CAR_REPAIR, service)
            if feature.get("Parts") or feature.get("CommercialParts"):
                apply_yes_no(Extras.CAR_PARTS, service, True)
            yield service

        if feature.get("Parts") or feature.get("CommercialParts"):
            parts = deepcopy(item)
            parts["ref"] = f"{item['ref']}_parts"
            apply_category(Categories.SHOP_CAR_PARTS, parts)
            yield parts
