from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider

FACILITIES_MAP = {
    "Deposit Taking ATM": Extras.ATM,
    "Non-Deposit Taking ATM": Extras.ATM,
    "Wheel Chair Friendly": Extras.WHEELCHAIR,
    "Wi-Fi": Extras.WIFI,
}
NEDBANK_SHARED_ATTRIBUTES = {
    "brand": "Nedbank",
    "brand_wikidata": "Q2751701",
}


class NedbankZASpider(JSONBlobSpider):
    name = "nedbank_za"
    item_attributes = NEDBANK_SHARED_ATTRIBUTES
    start_urls = ["https://personal.nedbank.co.za/contact/find-us.html"]
    locations_key = "data"

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.fetch_json)

    def fetch_json(self, response):
        auth_token = response.xpath('.//input[@id="authorizationtoken"]/@value').get()
        yield Request(
            url="https://api.nedsecure.co.za/nedbank/channeldistribution/v2/branches?resultsize=1000&latitude=-26&longitude=28",
            headers={"Authorization": auth_token},
            callback=self.parse,
            meta={"auth_token": auth_token},
        )

    def post_process_item(self, item, response, location):
        if location["type"] == "Physical Branch":
            apply_category(Categories.BANK, item)
        else:
            self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_type/{location['type']}")
            return
        item["ref"] = location["code"]
        for facility in location["facilities"]:
            if match := FACILITIES_MAP.get(facility["name"]):
                apply_yes_no(match, item, True)
            elif facility["name"] == "Wheel Chair Friendly with Staff Assistance*":
                item["extras"]["wheelchair"] = "limited"
                item["extras"]["wheelchair:description"] = "With staff assistance"
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unhandled_facility/{facility['name']}")
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        yield Request(
            url=f"https://api.nedsecure.co.za/nedbank/channeldistribution/v2/branches/{item['ref']}",
            headers={"Authorization": response.meta["auth_token"]},
            meta={"item": item},
            callback=self.parse_store,
        )

    def parse_store(self, response):
        item = response.meta["item"]
        location = response.json()["data"]
        item["opening_hours"] = OpeningHours()
        for day_hours in location["businessHours"]:
            if day_hours["openingHour"].lower() == "closed":
                item["opening_hours"].set_closed(day_hours["day"])
            else:
                item["opening_hours"].add_range(day_hours["day"], day_hours["openingHour"], day_hours["closingHour"])
        yield item
