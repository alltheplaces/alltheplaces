import re

from locations.categories import Categories, Drink, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import SocialMedia, set_social_media
from locations.storefinders.where2getit import Where2GetItSpider

branch_code_re = re.compile(r"(BG|GK|DH)[ +]*\d{3}$")


class DogHausUSSpider(Where2GetItSpider):
    name = "dog_haus_us"
    item_attributes = {"brand": "Dog Haus", "brand_wikidata": "Q105529843"}
    api_endpoint = "https://locations.doghaus.com/rest/getlist"
    api_key = "F9C9435A-1156-11EF-972B-1BEEB43C2251"

    def parse_item(self, item, location):
        item["ref"] = branch_code_re.search(item["name"]).group()
        item["branch"] = item.pop("name").removeprefix("DH-").removesuffix(item["ref"]).strip()
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        item["image"] = location["asset"]["Store Image 1"]["Image URL"]

        oh = OpeningHours()
        for day in DAYS_FULL:
            oh.add_range(day, location.get(f"{day.lower()}_open"), location.get(f"{day.lower()}_close"))
        item["opening_hours"] = oh

        set_social_media(item, SocialMedia.FACEBOOK, location["facebook_url"])
        set_social_media(item, SocialMedia.INSTAGRAM, location["instagram_url"])
        set_social_media(item, SocialMedia.YELP, location["yelp_url"])

        attributes = location["location"]["attributes"]
        self.apply_attribute(Extras.DELIVERY, item, attributes, "has_delivery")
        self.apply_attribute(Extras.PARKING_WHEELCHAIR, item, attributes, "has_wheelchair_accessible_parking")
        self.apply_attribute(Extras.TOILETS_WHEELCHAIR, item, attributes, "has_wheelchair_accessible_restroom")
        self.apply_attribute("toilets:unisex", item, attributes, "has_restroom_unisex")
        self.apply_attribute(PaymentMethods.CHEQUE, item, attributes, "pay_check")
        self.apply_attribute(PaymentMethods.DEBIT_CARDS, item, attributes, "pay_debit_card")
        self.apply_attribute(PaymentMethods.CONTACTLESS, item, attributes, "pay_mobile_nfc")
        self.apply_attribute(Extras.OUTDOOR_SEATING, item, attributes, "has_seating_outdoors")
        self.apply_attribute(Extras.DRIVE_THROUGH, item, attributes, "has_drive_through")
        self.apply_attribute(Extras.TAKEAWAY, item, attributes, "has_takeout")
        self.apply_attribute("fireplace", item, attributes, "has_fireplace")
        self.apply_attribute(Extras.LIVE_MUSIC, item, attributes, "has_live_music")
        self.apply_attribute(Drink.BEER, item, attributes, "serves_beer")
        self.apply_attribute(Drink.COCKTAIL, item, attributes, "serves_cocktails")
        self.apply_attribute(Drink.COFFEE, item, attributes, "serves_coffee")
        self.apply_attribute(Extras.HALAL, item, attributes, "serves_halal_food")
        self.apply_attribute("happy_hours", item, attributes, "serves_happy_hour_drinks")
        self.apply_attribute(Drink.LIQUOR, item, attributes, "serves_liquor")
        self.apply_attribute("organic", item, attributes, "serves_organic")
        self.apply_attribute("lunch:saladbar", item, attributes, "has_salad_bar")
        self.apply_attribute(Extras.VEGETARIAN, item, attributes, "serves_vegetarian")
        self.apply_attribute(Drink.WINE, item, attributes, "serves_wine")
        self.apply_attribute(Extras.BREAKFAST, item, attributes, "serves_breakfast")
        self.apply_attribute("lunch", item, attributes, "serves_lunch")
        self.apply_attribute("dinner", item, attributes, "serves_dinner")
        self.apply_attribute(Extras.BAR, item, attributes, "has_bar_onsite")
        self.apply_attribute(Extras.TOILETS, item, attributes, "has_restroom")
        self.apply_attribute(Extras.RESERVATION, item, attributes, "accepts_reservations")
        self.apply_attribute(Extras.VEGAN, item, attributes, "serves_vegan")
        self.apply_attribute(Extras.DOG, item, attributes, "welcomes_dogs")
        self.apply_attribute(PaymentMethods.CREDIT_CARDS, item, attributes, "pay_credit_card")
        self.apply_attribute(Extras.BABY_CHANGING_TABLE, item, attributes, "has_changing_tables")

        if (
            attributes.get("has_wheelchair_accessible_entrance") == "yes"
            and attributes.get("has_wheelchair_accessible_seating") == "yes"
        ):
            apply_yes_no(Extras.WHEELCHAIR, item, True)
        elif (
            attributes.get("has_wheelchair_accessible_entrance") == "no"
            and attributes.get("has_wheelchair_accessible_seating") == "no"
        ):
            apply_yes_no(Extras.WHEELCHAIR, item, False, False)
        elif (
            attributes.get("has_wheelchair_accessible_entrance") == "yes"
            or attributes.get("has_wheelchair_accessible_seating") == "yes"
        ):
            apply_yes_no(Extras.WHEELCHAIR_LIMITED, item, True)

        cards = set(attributes["pay_credit_card_types_accepted"])
        apply_yes_no(PaymentMethods.AMERICAN_EXPRESS, item, "american_express" in cards)
        apply_yes_no(PaymentMethods.DINERS_CLUB, item, "diners_club" in cards)
        apply_yes_no(PaymentMethods.DISCOVER_CARD, item, "discover" in cards)
        apply_yes_no(PaymentMethods.VISA, item, "visa" in cards)
        apply_yes_no(PaymentMethods.MASTER_CARD, item, "mastercard" in cards)
        cards.difference_update({"american_express", "discover", "visa", "mastercard", "diners_club"})
        assert cards == set(), cards

        item["extras"]["website:menu"] = attributes["url_menu"]
        item["extras"]["website:orders"] = attributes["url_order_ahead"]
        item["extras"]["website:booking"] = attributes.get("url_reservations")

        if attributes["has_catering"] == "yes":
            apply_category(Categories.CRAFT_CATERER, item)

        yield item

    def apply_attribute(self, attribute, item, attributes, key):
        apply_yes_no(attribute, item, attributes.get(key) == "yes", attributes.get(key, "unsure") == "unsure")
