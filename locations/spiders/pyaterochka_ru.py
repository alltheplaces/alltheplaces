import json

from scrapy import Spider

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class PyaterochkaRUSpider(Spider):
    name = "pyaterochka_ru"
    item_attributes = {"brand_wikidata": "Q1768969"}
    start_urls = ["https://5ka.ru/api/v2/stores/"]
    requires_proxy = True
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}  # To fetch quite big JSON

    def parse(self, response, **kwargs):
        data = json.loads(response.text[9:-2])  # Trim JS callback

        for store in data["data"]["features"]:
            # type=alco or store
            # alco is a department of type=store
            if store["properties"]["type"] != "store":
                continue

            item = Feature()
            item["ref"] = store["id"]
            item["lat"], item["lon"] = store["geometry"]["coordinates"]
            item["city"] = store["properties"]["city_name"]
            item["addr_full"] = store["properties"]["address"]

            if store["properties"]["is_24h"]:
                item["opening_hours"] = "24/7"
            else:
                oh = OpeningHours()
                for day in DAYS:
                    oh.add_range(
                        day,
                        store["properties"]["work_start_time"],
                        store["properties"]["work_end_time"],
                        time_format="%H:%M:%S",
                    )
                item["opening_hours"] = oh

            yield item
