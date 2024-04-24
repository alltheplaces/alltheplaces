import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.nandos import NANDOS_SHARED_ATTRIBUTES


class NandosZASpider(scrapy.Spider):
    name = "nandos_za"
    item_attributes = NANDOS_SHARED_ATTRIBUTES
    allowed_domains = ["api.locationbank.net"]
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=67b9c5e4-6ddf-4856-b3c0-cf27cfe53255"
    ]

    def parse(self, response):
        data = response.json()
        for i in data["locations"]:
            i["name"] = i.pop("locationName")
            i["phone"] = i.pop("primaryPhone")
            i["province"] = i.pop("administrativeArea")
            i["website"] = "https://store.nandos.co.za/details/" + i.pop("storeLocatorDetailsShortURL")
            item = DictParser.parse(i)

            oh = OpeningHours()
            for x in i["regularHours"]:
                oh.add_range(x["openDay"], x["openTime"], x["closeTime"])
            item["opening_hours"] = oh

            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in i["slAttributes"])
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in i["slAttributes"])
            apply_yes_no(Extras.WIFI, item, "WiFi" in i["slAttributes"])
            apply_yes_no(Extras.HALAL, item, "Halaal" in i["slAttributes"])
            apply_yes_no(Extras.KOSHER, item, "Kosher" in i["slAttributes"])
            # Unhandled: "Alcohol License", "Dine In", "Generator"

            yield item
