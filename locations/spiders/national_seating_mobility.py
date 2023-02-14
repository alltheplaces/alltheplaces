from locations.storefinders.store_locator_plus import StoreLocatorPlusSpider


class NationalSeatingMobilitySpider(StoreLocatorPlusSpider):
    name = "national_seating_mobility"
    item_attributes = {"brand": "National Seating & Mobility", "brand_wikidata": "Q116770969"}
    slp_dataset = "thegeneral_at_5by5agency_dot_com"
    slp_key = "myslp.982692489c53b1cb2b7209e3fe46a9650e9edca8026c572c989bbc9942a8d560"
