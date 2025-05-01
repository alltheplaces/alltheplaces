import re

from scrapy import Selector

from locations.hours import CLOSED_DE, DAYS_DE, OpeningHours, sanitise_day
from locations.spiders.lidl_gb import LidlGBSpider
from locations.storefinders.virtualearth import VirtualEarthSpider


class LidlDESpider(VirtualEarthSpider):
    name = "lidl_de"
    item_attributes = LidlGBSpider.item_attributes

    dataset_id = "ab055fcbaac04ec4bc563e65ffa07097"
    dataset_name = "Filialdaten-SEC/Filialdaten-SEC"
    api_key = "AnTPGpOQpGHsC_ryx9LY3fRTI27dwcRWuPrfg93-WZR2m-1ax9e9ghlD4s1RaHOq"

    def parse_item(self, item, feature, **kwargs):
        item["opening_hours"] = OpeningHours()

        days = Selector(text=feature["OpeningTimes"])
        for day_text in days.xpath("//text()").getall():
            day_text = re.sub(r"\s+", " ", day_text).strip()
            if not day_text:
                continue
            try:
                day_name, hours_text = day_text.split(" ", 1)
                day_name = sanitise_day(day_name, DAYS_DE)

                if hours_text.lower() in CLOSED_DE:
                    item["opening_hours"].set_closed(day_name)
                else:
                    open_time, close_time = hours_text.split("-")
                    item["opening_hours"].add_range(day_name, open_time, close_time)
            except ValueError:
                continue
        yield item
