import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature


class HruskaCZSpider(Spider):
    name = "hruska_cz"
    item_attributes = {"brand": "Hruška", "brand_wikidata": "Q58196374"}
    allowed_domains = ["mojehruska.cz"]
    start_urls = ["https://mojehruska.cz/prodejny/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for store in response.xpath('//div[@class="prodejny"]/div[position()>1]'):
            item = Feature()
            item["name"], item["ref"] = store.xpath("normalize-space(./div[1])").get().split(" č.", 1)
            item["addr_full"] = store.xpath("normalize-space(./div[2])").get()
            item["phone"] = store.xpath("normalize-space(./div[4])").get()
            item["opening_hours"] = oh = OpeningHours()
            for cell, default_days in ((5, ["Mo", "Tu", "We", "Th", "Fr"]), (6, ["Sa"]), (7, ["Su"])):
                for line in store.xpath(f"./div[{cell}]/text()").getall():
                    days = default_days
                    if match := re.match(r"([^\d:]+):\s*(.+)", line):
                        days = [DAYS_CZ[day.strip()] for day in match.group(1).split(",")]
                        line = match.group(2)
                    if line.strip().lower() == "zavřeno":
                        oh.set_closed(days)
                        continue
                    for start_time, end_time in re.findall(r"(\d{1,2}:\d{2})\s*[–-]\s*(\d{1,2}:\d{2})", line):
                        if start_time.zfill(5) < end_time.zfill(5):
                            oh.add_days_range(days, start_time, end_time)
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
