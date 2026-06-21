from locations.storefinders.location_bank import LocationBankSpider


class TigerWheelAndTyreZASpider(LocationBankSpider):
    name = "tiger_wheel_and_tyre_za"
    item_attributes = {"brand": "Tiger Wheel & Tyre", "brand_wikidata": "Q120762656"}
    start_urls = ["https://twtinfo.goreview.co.za/store-locator"]
    client_id = "9ac3bd9a-8edf-4cde-8b30-755940f3daa7"
