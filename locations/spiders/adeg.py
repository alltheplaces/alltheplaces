import json
from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, OpeningHours, sanitise_day


class AdegSpider(Spider):
    name = "adeg"
    item_attributes = {"brand": "ADEG", "brand_wikidata": "Q290211"}
    start_urls = ["https://www.adeg.at/services/maerkte-oeffnungszeiten"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath("//@data-merchant-content").get())
        for location in raw_data:
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["ref"] = location["uid"]
            item["website"] = "https://www.adeg.at" + item["website"]
            item["lat"], item["lon"] = location["coordinates"].split(",")
            oh = OpeningHours()
            for row in Selector(text=location["htmlTemplate"]).xpath(
                './/*[@class="opening-hours row"]//*[@class="text-nowrap"]'
            ):
                day = sanitise_day(row.xpath(".//span/text()").get().removesuffix(":"), DAYS_DE)
                time = row.xpath(".//span[2]/text()").get()
                if time:
                    open_time, close_time = time.split(" – ")
                    oh.add_range(day, open_time.strip(), close_time.strip())
            item["opening_hours"] = oh.as_opening_hours()
            yield item
