from locations.categories import Categories
from locations.json_blob_spider import JSONBlobSpider


class CashExpressZASpider(JSONBlobSpider):
    name = "cash_express_za"
    item_attributes = {
        "brand": "Cash Express",
        "brand_wikidata": "Q130262361",
        "extras": Categories.ATM.value,
    }
    start_urls = ["https://www.bidvestbank.co.za/assets/mock/cash-express-branded-atms.json"]

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("Device id")
        location["Latitude"] = location["Latitude"].replace(",", ".")
        location["Longitude"] = location["Longitude"].replace(",", ".")
        location["street_address"] = location.pop("Street Address")
