from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class SantaLollaBRSpider(Spider):
    name = "santa_lolla_br"
    item_attributes = {"brand": "Santa Lolla", "brand_wikidata": "Q28680413"}
    start_urls = ["https://www.santalolla.com.br/_v/get-stores"]

    def parse(self, response):
        for store in response.json():
            store["street_address"] = store.pop("street")
            if not store.get("latitude"):
                continue
            item = DictParser.parse(store)
            item["branch"] = item["ref"] = item.pop("name")
            oh = OpeningHours()
            for day in DAYS_FULL:
                try:
                    times = store["hour_" + day]
                    if times == "Fechado":
                        continue
                    start_time, _, end_time = times.split(" ")
                    if start_time.endswith("h"):
                        start_time += "00"
                    if end_time.endswith("h"):
                        end_time += "00"
                    oh.add_range(day, start_time, end_time, time_format="%Hh%M")
                except:
                    continue
            item["opening_hours"] = oh
            apply_category(Categories.SHOP_SHOES, item)
            yield item
