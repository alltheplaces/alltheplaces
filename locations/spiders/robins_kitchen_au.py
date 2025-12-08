from scrapy import Request, Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class RobinsKitchenAUSpider(Spider):
    name = "robins_kitchen_au"
    item_attributes = {
        "brand": "Robins Kitchen",
        "brand_wikidata": "Q126175864",
        "extras": Categories.SHOP_HOUSEWARE.value,
    }
    allowed_domains = ["www.robinskitchen.com.au"]
    start_urls = ["https://www.robinskitchen.com.au/api/get-stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, method="POST")

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)

            item["branch"] = item["name"].replace("Robins Kitchen ", "")
            item["geometry"] = location["location"]
            item["street_address"] = clean_address([location["address1"], location["address2"]])
            item["website"] = "https://www.robinskitchen.com.au/stores/" + location["slug"]

            item["opening_hours"] = OpeningHours()
            for day_name, hours in location["storeHours"].items():
                if hours["open"] == "-" or hours["close"] == "-":
                    continue
                item["opening_hours"].add_range(
                    day_name.title(),
                    hours["open"].replace(".", ":").strip(),
                    hours["close"].replace(".", ":").replace(":-", ":").strip(),
                )

            yield item
