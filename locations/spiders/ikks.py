import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours


class IkksSpider(scrapy.Spider):
    name = "ikks"
    item_attributes = {"brand": "IKKS", "brand_wikidata": "Q3146711"}
    allowed_domains = ["stores.ikks.com"]
    start_urls = ["https://stores.ikks.com/mobify/proxy/ocapi/s/IKKS_COM/dw/shop/v21_3/stores?latitude=24.3356791&longitude=23.769953599999997&max_distance=20000&delivery_method=delivery&client_id=1c53da3a-3640-4a31-adad-0f43be6c0904&start=0&count=200"]

    def parse(self, response):
        if not response.json().get("count"):
            return
        for data in response.json().get("data"):
            if "IKKS" in data.get("c_commercialSign"):
                item = DictParser.parse(data)
                if not data.get("store_hours"):
                    continue
                opening_hours = []
                for row in data.get("store_hours").split(","):
                    for helfday in row.split("/"):
                        days = re.findall("[a-z]+-[a-z]+|[a-z]+", row)[0].split("-")
                        hours = re.findall("[0-9]{2}:[0-9]{2} - [0-9]{2}:[0-9]{2}", helfday)
                        if len(days) == 2:
                            openinghour = f"{DAYS_FR[days[0].title()[:2]]}-{DAYS_FR[days[1].title()[:2]]} {hours[0]}"
                        else:
                            openinghour = f"{DAYS_FR[days[0].title()[:2]]} {hours[0]}"
                        opening_hours.append(openinghour)
                oh = OpeningHours()
                oh.from_linked_data({"openingHours": opening_hours})
                item["opening_hours"] = oh.as_opening_hours()

                yield item

        start = int(re.findall('start=[0-9]+', response.url)[0][6:]) + 200
        url = f"https://stores.ikks.com/mobify/proxy/ocapi/s/IKKS_COM/dw/shop/v21_3/stores?latitude=24.3356791&longitude=23.769953599999997&max_distance=20000&delivery_method=delivery&client_id=1c53da3a-3640-4a31-adad-0f43be6c0904&start={start}&count=200"
        yield scrapy.Request(url=url, callback=self.parse)