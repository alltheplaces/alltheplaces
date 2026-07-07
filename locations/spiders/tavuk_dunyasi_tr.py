import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class TavukDunyasiTRSpider(Spider):
    name = "tavuk_dunyasi_tr"
    item_attributes = {"brand": "Tavuk Dünyası", "brand_wikidata": "Q126924105"}
    start_urls = ["https://www.tavukdunyasi.com/umbraco/surface/Common/GetAllRestaurants?culture=tr-TR&searchText="]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            if name := item.pop("name", None):
                item["branch"] = name.strip()
            item["ref"] = location["code"]
            item["street_address"] = item.pop("addr_full")
            item["lat"] = location["latitude"].replace(",", ".")
            item["lon"] = location["longitude"].replace(",", ".")
            item["extras"]["addr:district"] = location["district"]

            if times := re.findall(r"\d{1,2}:\d{2}", location.get("workingHour") or ""):
                if len(times) == 2:
                    open_time, close_time = times
                    if close_time == "00:00":
                        close_time = "24:00"
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_days_range(DAYS, open_time, close_time)

            apply_category(Categories.FAST_FOOD, item)
            yield item
