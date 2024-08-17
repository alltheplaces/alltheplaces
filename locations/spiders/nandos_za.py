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
    web_root = "https://store.nandos.co.za/details/"

    def parse(self, response):
        data = response.json()
        for i in data["locations"]:
            i["phone"] = i.pop("primaryPhone")
            if i["additionalPhone1"]:
                i["phone"] += "; " + i.pop("additionalPhone1")
            i["province"] = i.pop("administrativeArea")
            i["website"] = self.web_root + i.pop("storeLocatorDetailsShortURL")
            if i["addressLine2"]:
                i["addressLine1"] += ", " + i.pop("addressLine2")
            item = DictParser.parse(i)

            item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()

            oh = OpeningHours()
            for x in i["regularHours"]:
                oh.add_range(x["openDay"], x["openTime"], x["closeTime"])
            item["opening_hours"] = oh

            apply_yes_no(Extras.BACKUP_GENERATOR, item, "Generator" in i["slAttributes"])
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in i["slAttributes"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive Thru" in i["slAttributes"])
            apply_yes_no(Extras.HALAL, item, "Halaal" in i["slAttributes"])
            apply_yes_no(Extras.KOSHER, item, "Kosher" in i["slAttributes"])
            apply_yes_no(Extras.TAKEAWAY, item, "Collect" in i["slAttributes"])
            apply_yes_no(Extras.WIFI, item, "WiFi" in i["slAttributes"])
            # Unhandled: "Alcohol License", "Dine In"

            yield item
