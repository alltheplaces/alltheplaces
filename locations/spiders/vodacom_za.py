from locations.categories import Categories
from locations.storefinders.location_bank import LocationBankSpider


class VodacomZASpider(LocationBankSpider):
    name = "vodacom_za"
    client_id = "19ced8ad-ae12-440c-abb5-423a1d49a002"
    item_attributes = {
        "brand": "Vodacom",
        "brand_wikidata": "Q1856518",
        "extras": Categories.SHOP_MOBILE_PHONE.value,
    }
