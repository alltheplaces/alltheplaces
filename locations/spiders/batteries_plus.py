import json

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.storefinders.where2getit import Where2GetItSpider


class BatteriesPlusSpider(Where2GetItSpider):
    name = "batteries_plus"
    item_attributes = {"brand": "Batteries Plus Bulbs", "brand_wikidata": "Q17005157"}
    api_endpoint = "https://www.batteriesplus.com/store-locator/rest/getlist"
    api_key = "9C5DD3EE-C1E6-11EE-903D-65C0A96E38C4"

    def parse_item(self, item, location):
        item["branch"] = item.pop("name")
        item["ref"] = location["localpage_url_id"].removeprefix("batteries-plus-")
        set_social_media(item, SocialMedia.YELP, location["yelp_url"])

        attributes = {attribute["id"]: attribute["value"] for attribute in json.loads(location["attributes"])}
        self.apply_attribute(PaymentMethods.DEBIT_CARDS, item, attributes, "pay_debit_card")
        self.apply_attribute(PaymentMethods.CREDIT_CARDS, item, attributes, "pay_credit_card")
        self.apply_attribute("recycling:electrical_appliances", item, attributes, "has_recycling_electronics")
        self.apply_attribute(Extras.TAKEAWAY, item, attributes, "has_in_store_pickup")
        self.apply_attribute("recycling:batteries", item, attributes, "has_recycling_batteries")

        oh = OpeningHours()
        for day, (opening, closing) in zip(DAYS_FROM_SUNDAY, location["bho"]):
            if "9999" not in (opening, closing):
                oh.add_range(day, opening, closing, time_format="%H%M")
        item["opening_hours"] = oh

        payment_forms = set(json.loads(location["payment_forms"]))
        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "American Express" in payment_forms)
        apply_yes_no(PaymentMethods.APPLE_PAY, item, "Apple Pay" in payment_forms)
        apply_yes_no(PaymentMethods.CASH, item, "Cash" in payment_forms)
        apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "Discover" in payment_forms)
        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "Google Pay" in payment_forms)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "Mastercard" in payment_forms)
        apply_yes_no(PaymentMethods.VISA, item, "Visa" in payment_forms)

        yield item

    def apply_attribute(self, attribute, item, attributes, key):
        apply_yes_no(attribute, item, attributes.get(key) == "yes", attributes.get(key, "unsure") == "unsure")
