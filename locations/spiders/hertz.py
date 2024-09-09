from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, FuelCards, PaymentMethods, apply_yes_no
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

PAYMENT_MAP = {
    "AMEX": PaymentMethods.AMERICAN_EXPRESS,
    "AMX": PaymentMethods.AMERICAN_EXPRESS,
    "AXP": PaymentMethods.AMERICAN_EXPRESS,
    "CHINAUNIONPAY": PaymentMethods.UNIONPAY,
    "CHQ": PaymentMethods.CHEQUE,
    "CSH": PaymentMethods.CASH,
    "CUP": PaymentMethods.UNIONPAY,
    "DC": PaymentMethods.DISCOVER_CARD,
    "DINERS": PaymentMethods.DINERS_CLUB,
    "DISC": PaymentMethods.DISCOVER_CARD,
    "DISCOVER": PaymentMethods.DISCOVER_CARD,
    "DKV": FuelCards.DKV,
    "JCB": PaymentMethods.JCB,
    "MASTER": PaymentMethods.MASTER_CARD,
    "MASTERDEBIT": PaymentMethods.MASTER_CARD_DEBIT,
    "MC": PaymentMethods.MASTER_CARD,
    "UTA": FuelCards.UTA,
    "VISA": PaymentMethods.VISA,
    "VISADEBIT": PaymentMethods.VISA_DEBIT,
    # TODO: CRQ, DB, ECH, FCH, HCC, VCH
}


class HertzSpider(JSONBlobSpider):
    name = "hertz"
    item_attributes = {"extras": Categories.CAR_RENTAL.value}  # "brand" is applied in code
    locations_key = "data"
    custom_settings = {"CONCURRENT_REQUESTS": 4}  # Let's be more gentle with the API

    def start_requests(self):
        for lat, lon in point_locations("earth_centroids_iseadgg_346km_radius.csv"):
            yield Request(
                f"https://ecom.mss.hertz.io/mdm-locations/internal-lookup/geo-search/hertz/?lat={lat}&long={lon}&radius=1000&locationTypes=AP,HT,LC,FB,CR,RA,BT,BS,DL,AT,TF"
            )

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("address") or {})
        feature.update(feature.pop("contact_info") or {})
        feature["name"].removeprefix("Hertz Car Rental - ").removeprefix("Hertz Truck Rental - ")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["oag"]

        self.crawler.stats.inc_value(f"atp/{self.name}/ownership_type/{feature.get('ownership_type')}")

        if feature.get("ownership_type", "").lower() in ["corporate", "licensee"]:
            # Only apply the brand for corporate and licensee locations
            item["brand"] = "Hertz"
            item["brand_wikidata"] = "Q1543874"
            item["branch"] = item.pop("name")

        item["extras"]["fax"] = feature.get("fax")
        if feature.get("phone"):
            item["phone"] = feature.get("phone", {}).get("international_phone_number")

        item["website"] = feature["website_urls"]["full_url"]

        item["street_address"] = merge_address_lines([feature["address1"], feature["address2"]])
        item["country"] = feature["country_short"]
        item["state"] = feature["state_short"]
        self.crawler.stats.inc_value(f"atp/{self.name}/country/{item['country']}")

        oh = OpeningHours()
        for day_idx, day_hours in feature["curated_days"].items():
            day = DAYS[int(day_idx) - 1]
            for hours in day_hours:
                oh.add_range(day, hours["start_time"], hours["end_time"])
        item["opening_hours"] = oh

        if payment_methods := feature.get("allowed_payment_methods"):
            for payment in payment_methods:
                if payment_tag := PAYMENT_MAP.get(payment):
                    apply_yes_no(payment_tag, item, True)

        yield item
