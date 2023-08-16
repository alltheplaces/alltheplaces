import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours


class BabyBuntingSpider(scrapy.Spider):
    name = "baby_bunting"
    item_attributes = {
        "brand": "Baby Bunting",
        "brand_wikidata": "Q109626935",
    }
    allowed_domains = ["www.babybunting.com.au"]

    def start_requests(self):
        yield JsonRequest(
            url="https://www.babybunting.com.au/api/cnts/getAllFromType",
            data=[{"type": "store"}],
            method="POST",
        )

    def parse(self, response):
        for store in response.json():
            if (
                "COMING SOON" in store["title"].upper()
                or len(list(filter(lambda h: ("CLOSED" in h.upper()), store["opening_hours"].values()))) > 0
            ):
                continue
            item = DictParser.parse(store)
            item["ref"] = str(store["supplychannel_id"])
            item["lat"] = store["address_lat_lng"].replace(" ", "").split(",")[0]
            item["lon"] = store["address_lat_lng"].replace(" ", "").split(",")[1]
            item["addr_full"] = store["address_text"].replace("\xa0", " ")
            item["postcode"] = str(item["postcode"])
            item["country"] = "AU"
            if "lat" in item and "lon" in item:
                if float(item["lon"]) > 166.42 and float(item["lat"]) < 34.42:
                    item["country"] = "NZ"
            item["website"] = "https://www.babybunting.com.au/find-a-store/" + item["website"]
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                open_key = day.lower() + "_from"
                close_key = day.lower() + "_to"
                if open_key in store["opening_hours"] and close_key in store["opening_hours"]:
                    open_time = store["opening_hours"][open_key].replace(" ", "").replace(".", ":")
                    close_time = store["opening_hours"][close_key].replace(" ", "").replace(".", ":")
                    item["opening_hours"].add_range(DAYS_EN[day], open_time, close_time, "%I:%M%p")
            yield (item)
