import re
from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.ssangyong_kr import SSANGYONG_SHARED_ATTRIBUTES


class SsangyongAUSpider(JSONBlobSpider):
    name = "ssangyong_au"
    item_attributes = SSANGYONG_SHARED_ATTRIBUTES
    allowed_domains = ["kgm.com.au"]
    start_urls = ["https://kgm.com.au/dealers"]

    services = [
        ("IsSalesStore", "Sales", "Dealer", Categories.SHOP_CAR),
        ("IsServiceStore", "Service", "Service", Categories.SHOP_CAR_REPAIR),
        ("IsPartsStore", "Parts", "Parts", Categories.SHOP_CAR_PARTS),
    ]

    def extract_json(self, response: TextResponse) -> list[dict]:
        for script in response.xpath('//script[contains(text(), "self.__next_f.push([1,")]/text()').getall():
            chunk = parse_js_object(script)
            if len(chunk) > 1 and isinstance(chunk[1], str) and '"dealers":[' in chunk[1]:
                return parse_js_object(chunk[1].split('"dealers":', 1)[1])
        return []

    def pre_process_data(self, feature: dict) -> None:
        feature["latitude"] = feature.pop("DealerLatitude", None)
        feature["longitude"] = feature.pop("DealerLongitude", None)
        feature["addr_full"] = feature.pop("DealerAddress", None)
        feature["state"] = feature.pop("DealerState", None)
        feature["postcode"] = str(feature.pop("DealerPostcode", "") or "")
        feature["ref"] = feature.pop("DealerCode", None)
        if website := feature.pop("DealerWebsite", None):
            feature["website"] = website if website.startswith("http") else "https://" + website

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = re.sub(r"\s*\b(?:KGM|SsangYong)\b\s*", " ", feature.get("Dealership", "")).strip()
        for flag, suffix, prefix, category in self.services:
            if not feature.get(flag):
                continue
            service_item = item.deepcopy()
            service_item["ref"] = f"{item['ref']}_{suffix}"
            service_item["phone"] = feature.get(f"{prefix}Telephone")
            service_item["email"] = feature.get(f"{prefix}Email")
            service_item["opening_hours"] = OpeningHours()
            service_item["opening_hours"].add_ranges_from_string(
                "Mon-Fri: {}, Sat: {}, Sun: {}".format(
                    feature.get(f"{prefix}OpenMonFri") or "closed",
                    feature.get(f"{prefix}OpenSaturday") or "closed",
                    feature.get(f"{prefix}OpenSunday") or "closed",
                )
            )
            apply_category(category, service_item)
            yield service_item
