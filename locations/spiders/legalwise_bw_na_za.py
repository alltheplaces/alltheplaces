import json
import re
from typing import Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class LegalwiseBWNAZASpider(Spider):
    name = "legalwise_bw_na_za"
    item_attributes = {"brand": "LegalWise", "brand_wikidata": "Q61442307"}
    start_urls = ["https://www.legalwise.co.za/branches"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        raw_data = json.loads(
            re.search(
                r"branches\s*=\s*(\[.+\]);\s*", response.xpath('//*[contains(text(),"postalCode")]/text()').get()
            ).group(1)
        )
        for location in raw_data:
            item = DictParser.parse(location)
            item["website"] = urljoin("https://www.legalwise.co.za/branches/", location.get("slug"))
            oh = OpeningHours()
            for day_time in location.get("regularHours"):
                day = day_time.get("day")
                open_time = day_time.get("openTime")
                close_time = day_time.get("closeTime")
                oh.add_range(day=day, open_time=open_time, close_time=close_time)
            item["opening_hours"] = oh
            apply_category(Categories.OFFICE_INSURANCE, item)
            yield item
