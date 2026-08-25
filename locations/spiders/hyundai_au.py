from collections import defaultdict
from typing import Iterable
from urllib.parse import urlparse

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiAUSpider(JSONBlobSpider):
    name = "hyundai_au"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundai.com"]
    no_refs = True
    start_urls = ["https://www.hyundai.com/content/api/au/hyundai/v3/findadealer?postcode=0"]

    def parse(self, response: Response) -> Iterable[Feature]:
        groups = [response.json()["allDealers"][key] for key in ("dealers", "serviceDealers", "partsDealers")]

        dealers_by_address = defaultdict(set)
        for group in groups:
            for feature in group:
                for address in self.email_addresses(feature):
                    dealers_by_address[address.lower()].add(feature.get("dealerCode") or feature.get("tradingName"))
        self.dealer_addresses = {address for address, dealers in dealers_by_address.items() if len(dealers) == 1}

        for group in groups:
            yield from self.parse_feature_array(response, group) or []

    @staticmethod
    def email_addresses(feature: dict) -> list[str]:
        return [address.strip() for address in (feature.get("email") or "").split(";") if address.strip()]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("closed"):
            return

        item["name"] = feature.get("tradingName") or feature.get("dealerCode")
        item["street_address"] = item.pop("street")
        item["email"] = next(
            (address for address in self.email_addresses(feature) if address.lower() in self.dealer_addresses), None
        )
        if item.get("website") and not urlparse(item["website"]).hostname:
            item["website"] = None

        if "testDriveModels" in feature.keys():
            apply_category(Categories.SHOP_CAR, item)
        elif "newWinBkAServiceMobile" in feature.keys():
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            apply_category(Categories.SHOP_CAR_PARTS, item)

        yield item
