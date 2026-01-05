from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class SantaLollaBRSpider(Spider):
    name = "santa_lolla_br"
    item_attributes = {"brand": "Santa Lolla", "brand_wikidata": "Q28680413"}
    no_refs = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.santalolla.com.br/api/dataentities/SL/search?_fields=isKiosk,business_hours,city,closed,email,hour_Friday,hour_holiday,hour_Monday,hour_Saturday,hour_Sunday,hour_Thursday,hour_Tuesday,hour_Wednesday,latitude,longitude,name,number,phone,phone2,photo,postal_code,state,street,whatsapp",
            headers={
                "REST-Range": "resources=0-1000",
            },
        )

    def parse(self, response):
        for store in response.json():
            store["street-address"] = store.pop("street")
            item = DictParser.parse(store)
            if name := item.pop("name"):
                item["branch"] = name.replace("Santa Lolla", "").lstrip()
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
