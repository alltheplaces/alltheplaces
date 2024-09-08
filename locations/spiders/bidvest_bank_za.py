from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class BidvestBankZASpider(JSONBlobSpider):
    name = "bidvest_bank_za"
    item_attributes = {
        "brand": "Bidvest Bank",
        "brand_wikidata": "Q4904284",
        "extras": Categories.ATM.value,
    }
    start_urls = ["https://www.bidvestbank.co.za/assets/mock/bidvest-branded-atms.json"]

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("Device id")
        location["Latitude"] = location["Latitude"].replace(",", ".")
        location["Longitude"] = location["Longitude"].replace(",", ".")
        location["street_address"] = location.pop("Street Address")
