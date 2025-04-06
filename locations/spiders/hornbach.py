from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_CH, OpeningHours, day_range


class HornbachSpider(scrapy.Spider):
    name = "hornbach"
    BODENHAUS = {"name": "Bodenhaus", "brand": "Bodenhaus"}
    HORNBACH = {"brand": "HORNBACH", "brand_wikidata": "Q685926"}
    start_urls = [
        "https://www.hornbach.de/hornbach/cms/de/de/technik/alle-maerkte/alle-maerkte.json",
        "https://www.hornbach.at/hornbach/cms/at/de/technik/alle-maerkte/alle-maerkte.json",
        "https://www.hornbach.ch/hornbach/cms/ch/de/technik/alle-maerkte/alle-maerkte.json",
        "https://www.hornbach.lu/hornbach/cms/lu/de/technik/alle-maerkte/alle-maerkte.json",
    ]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_HANDLERS": {"https": "scrapy.core.downloader.handlers.http2.H2DownloadHandler"},
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["stores"]:
            item = DictParser.parse(store)

            if item["name"].startswith("BODENHAUS "):
                item["branch"] = item.pop("name").removeprefix("BODENHAUS ")
                item.update(self.BODENHAUS)
                apply_category(Categories.SHOP_FLOORING, item)
            elif item["name"].startswith("HORNBACH "):
                item["branch"] = item.pop("name").removeprefix("HORNBACH ")
                item.update(self.HORNBACH)

            oh = OpeningHours()
            for time in store["regularTimes"]:
                if "-" in time["day"]:
                    start, end = time["day"].replace(".", "").replace(" ", "").split("-", maxsplit=1)
                    if "hornbach.ch" in store["url"]:
                        start = DAYS_CH.get(start)
                        end = DAYS_CH.get(end)
                    oh.add_days_range(day_range(start, end), time["from"], time["until"])
                else:
                    day = time["day"].replace(".", "").replace(" ", "")
                    if "hornbach.ch" in store["url"]:
                        day = DAYS_CH.get(day)
                    oh.add_range(day, time["from"], time["until"], time_format="%H:%M")
            item["opening_hours"] = oh
            yield item
