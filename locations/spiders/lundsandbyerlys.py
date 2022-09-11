# -*- coding: utf-8 -*-
import datetime
import scrapy
from locations.dict_parser import DictParser


class LundsAndByerlysSpider(scrapy.Spider):
    name = "lundsandbyerlys"
    item_attributes = {"brand": "Lunds & Byerlys", "brand_wikidata": "Q19903424"}
    allowed_domains = ["lundsandbyerlys.com"]
    start_urls = [
        "https://lundsandbyerlys.com/wp-admin/admin-ajax.php?action=store_search&autoload=1",
    ]

    def parse_hours(self, hours):
        if not hours:
            return ""

        hours = hours.strip()
        hours = hours.replace("<p>", "").replace("</p>", "")
        from_time, to_time = hours.split(" - ")
        from_time = datetime.datetime.strptime(from_time, "%I:%M %p").strftime("%H:%M")
        to_time = datetime.datetime.strptime(to_time, "%I:%M %p").strftime("%H:%M")
        if to_time == "00:00":
            to_time = "24:00"

        return f"Mo-Su {from_time}-{to_time}"

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)

            item["street_address"] = ", ".join(
                filter(None, [store["address"], store["address2"]])
            )
            item["addr_full"] = None
            item["website"] = response.urljoin(store["url"])
            item["name"] = store["store"]
            item["opening_hours"] = self.parse_hours(store["hours"])

            yield item
