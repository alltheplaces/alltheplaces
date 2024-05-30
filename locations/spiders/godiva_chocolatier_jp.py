from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class GodivaChocolatierJPSpider(Spider):
    name = "godiva_chocolatier_jp"
    item_attributes = {
        "brand": "Godiva Chocolatier",
        "brand_wikidata": "Q931084",
        "extras": Categories.SHOP_CHOCOLATE.value,
    }
    allowed_domains = ["shop.godiva.co.jp"]
    start_urls = ["https://shop.godiva.co.jp/api/delivery/stores/search/"]

    def start_requests(self):
        data = {
            "lat": "",
            "lng": "",
            "area_id": "",
            "q": "",
            "is_opening": "",
            "bs_services": "",
            "bs_brands": "",
            "referer": "",
            "_browser_url": "https://shop.godiva.co.jp/stores",
            "current_url": "https://shop.godiva.co.jp/stores",
            "limit": "10000",
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def parse(self, response):
        for location in response.json()["data"]["items"]:
            item = DictParser.parse(location)
            item["lat"], item["lon"] = location.get("location").split(",", 1)
            item["addr_full"] = clean_address([location.get("addressExtra"), location.get("address")])

            if location.get("image"):
                item["image"] = location["image"][0].get("1024")

            item["opening_hours"] = OpeningHours()
            hours_string = ""
            for day_hours in location.get("weekday_opens", []):
                for time_period in day_hours["data"]["time"]:
                    hours_string = "{} {}: {} - {}".format(
                        hours_string, day_hours["data"]["name_en"], time_period["start"], time_period["end"]
                    )
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
