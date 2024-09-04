from scrapy import Request, Spider

from locations.categories import Categories, FuelCards, PaymentMethods, apply_yes_no
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
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


class HertzSpider(Spider):
    name = "hertz"
    item_attributes = {"extras": Categories.CAR_RENTAL.value}  # "brand" is applied in code

    def start_requests(self):
        for lat, lon in point_locations("earth_centroids_iseadgg_346km_radius.csv"):
            yield Request(
                f"https://ecom.mss.hertz.io/mdm-locations/internal-lookup/geo-search/hertz/?lat={lat}&long={lon}&radius=347"
            )

    def parse(self, response):
        for location in response.json()["data"]:
            item = Feature()

            name = location["name"].removeprefix("Hertz Car Rental - ").removeprefix("Hertz Truck Rental - ")
            if location.get("ownership_type") == "CORPORATE":
                # Only apply brand tags to "Corporate" type locations
                item["brand"] = "Hertz"
                item["brand_wikidata"] = "Q1543874"
                item["branch"] = name
            else:
                item["name"] = name

            item["extras"]["fax"] = location["contact_info"]["fax"]
            item["email"] = location["contact_info"]["email"]
            item["website"] = location["website_urls"]["full_url"]
            item["ref"] = location["oag"]

            item["street_address"] = merge_address_lines(
                [location["address"]["address1"], location["address"]["address2"]]
            )
            item["city"] = location["address"]["city"]
            item["lat"] = location["address"]["latitude"]
            item["country"] = location["address"]["country_short"]
            item["postcode"] = location["address"]["postal_code"]
            item["state"] = location["address"]["state_short"]
            item["lon"] = location["address"]["longitude"]

            if location["contact_info"]["phone"]:
                item["phone"] = location["contact_info"]["phone"]["international_phone_number"]

            oh = OpeningHours()
            for day_idx, day_hours in location["curated_days"].items():
                day = DAYS[int(day_idx) - 1]
                for hours in day_hours:
                    oh.add_range(day, hours["start_time"], hours["end_time"])
            item["opening_hours"] = oh

            if location.get("allowed_payment_methods"):
                for payment in location["allowed_payment_methods"]:
                    if payment_tag := PAYMENT_MAP.get(payment):
                        apply_yes_no(payment_tag, item, True)

            yield item
