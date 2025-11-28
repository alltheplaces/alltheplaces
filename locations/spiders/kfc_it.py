import json

from scrapy import Spider

from locations.categories import apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcITSpider(Spider):
    name = "kfc_it"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://www.kfc.it/ristoranti"]

    def parse(self, response):
        data_raw = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        locations = json.loads(data_raw)["props"]["pageProps"]["data"]["items"]
        for store in locations:
            store.update(store.pop("labels"))
            item = DictParser.parse(store)
            item["extras"]["province"] = store["province"]
            item["housenumber"] = store["address_number"]
            item["branch"] = store["title"]
            item.pop("name", None)
            item.pop("state", None)
            item["opening_hours"] = oph = OpeningHours()
            if hours := list(filter(lambda tt: tt["id"] == "store", store["timetables"]))[-1]:
                for day in hours["times"]:
                    for hour in day["hour"]:
                        oph.add_ranges_from_string(f"{day['label_day']} {hour}", days=DAYS_IT)
                    if not day["hour"]:
                        oph.add_range(DAYS_IT[day["label_day"]], "closed", "closed")
            accessible = any(map(lambda s: s["code"] == "DISABLED", store["services"]))
            apply_yes_no("wheelchair", item, accessible, apply_positive_only=False)
            item["street_address"] = item.pop("addr_full", None)
            yield item
