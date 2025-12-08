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
            apply_category(Categories.SHOP_CAR, item)
            if feature.get("Service") or feature.get("CommercialService"):
                apply_yes_no(Extras.CAR_REPAIR, item, True)
            if feature.get("Parts") or feature.get("CommercialParts"):
                apply_yes_no(Extras.CAR_PARTS, item, True)
        elif feature.get("Service") or feature.get("CommercialService"):
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            if feature.get("Parts") or feature.get("CommercialParts"):
                apply_yes_no(Extras.CAR_PARTS, item, True)
        elif feature.get("Parts") or feature.get("CommercialParts"):
            apply_category(Categories.SHOP_CAR_PARTS, item)
        else:
            apply_category(Categories.SHOP_CAR, item)
        yield item
