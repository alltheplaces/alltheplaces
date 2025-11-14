import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class BricoBELUSpider(SitemapSpider):
    name = "brico_be_lu"
    item_attributes = {"brand": "Brico", "brand_wikidata": "Q2510786"}
    sitemap_urls = ["https://www.brico.be/fr/store/sitemap.xml"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if data := re.search(
            r"preLoadedStoreData\"\s*:\s*({.*}),\"address",
            response.xpath('//*[contains(text(),"markers")]/text()').get(),
        ):
            raw_data = json.loads(data.group(1))
            item = DictParser.parse(raw_data)
            item.pop("name")
            item["ref"] = item["website"] = response.url
            item["branch"] = raw_data["displayName"]
            item["street_address"] = merge_address_lines([raw_data["address"]["line2"], raw_data["address"]["line1"]])
            oh = OpeningHours()
            for day_time in raw_data["openingHours"]["weekDayOpeningList"]:
                day = sanitise_day(day_time["weekDay"], DAYS_FR)
                if day_time["closed"]:
                    oh.set_closed(day)
                else:
                    open_time = day_time["openingTime"]["formattedHour"]
                    close_time = day_time["closingTime"]["formattedHour"]
                    oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
            yield item
