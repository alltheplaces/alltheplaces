import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class Mitre10NZSpider(scrapy.Spider):
    name = "mitre_10_nz"
    item_attributes = {"brand": "Mitre 10", "brand_wikidata": "Q6882394"}
    allowed_domains = ["www.mitre10.co.nz"]
    start_urls = ["https://www.mitre10.co.nz/store-locator?branchId=X1&page=0&type=data"]

    def parse(self, response):
        current_page = response.meta.get("page", 0)
        total_stores = response.json()["total"]
        stores = response.json()["data"]
        for store in stores:
            item = DictParser.parse(store)
            item["ref"] = store["storeCode"]
            item["name"] = store["displayName"]
            item.pop("website")
            if len(store["storeLandingUrl"]) > 0:
                if store["storeLandingUrl"][0] == "/":
                    item["website"] = "https://www.mitre10.co.nz/store" + store["storeLandingUrl"]
                else:
                    item["website"] = store["storeLandingUrl"]
            oh = OpeningHours()
            for day in DAYS_FULL:
                if day in store["openings"]:
                    hours_raw = "".join(store["openings"][day].split())
                elif day.upper() in store["openings"]:
                    hours_raw = "".join(store["openings"][day.upper()].split())
                else:
                    continue
                if hours_raw == "Closed":
                    continue
                open_time = hours_raw.split("-")[0]
                close_time = hours_raw.split("-")[1]
                oh.add_range(day, open_time, close_time, "%I:%M%p")
            item["opening_hours"] = oh.as_opening_hours()
            yield item
        if current_page * 10 < total_stores - 10:
            next_page = current_page + 1
            yield scrapy.Request(
                url=f"https://www.mitre10.co.nz/store-locator?branchId=X1&page={next_page}&type=data",
                callback=self.parse,
                meta={"page": next_page},
            )
