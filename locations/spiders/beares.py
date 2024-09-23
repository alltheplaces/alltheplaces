from scrapy import Request

from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

BEARES_COUNTRIES = {
    "101": "BW",
    "155": "LS",
    "182": "NA",
    "73": "ZA",
    "219": "SZ",
}


class BearesSpider(JSONBlobSpider):
    name = "beares"
    item_attributes = {"brand": "Beares", "brand_wikidata": "Q116474908"}
    start_urls = ["https://beares.co.za/controllers/get_locations.php"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                body="param1=Beares",
            )

    def pre_process_data(self, location):
        location["phone"] = "; ".join([location.get("Phone"), location.get("Phone2"), location.get("Phone3")])

    def post_process_item(self, item, response, location):
        item["branch"] = location.get("StoreLocatorName")
        item["country"] = BEARES_COUNTRIES.get(location["CountryId"])
        if item["postcode"] in ["9000", "9999"] and item["country"] != "ZA":
            item.pop("postcode")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string("Mon-Fri " + location.get("TradingMonFri"))
        item["opening_hours"].add_ranges_from_string("Sat " + location.get("TradingSat"))
        item["opening_hours"].add_ranges_from_string("Sun " + location.get("TradingSunPub"))
        yield item
