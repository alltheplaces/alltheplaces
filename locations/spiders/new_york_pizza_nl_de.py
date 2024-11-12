import re
from typing import Iterable

import scrapy
from scrapy import Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_DE, DAYS_EN, OpeningHours


class NewYorkPizzaNLDESpider(Spider):
    name = "new_york_pizza_nl_de"
    item_attributes = {"brand": "New York Pizza", "brand_wikidata": "Q2639128"}

    def start_requests(self) -> Iterable[Request]:
        for country, page in (("nl", "vestigingen"), ("de", "filialen")):
            yield scrapy.Request(
                f"https://www.newyorkpizza.{country}/{page}",
                callback=self.parse_auth_token,
                cb_kwargs={"top_level_domain": country},
            )

    def parse_auth_token(self, response: Response, top_level_domain: str = None) -> Iterable[Request]:
        auth_token = response.xpath('//input[@id="completeAntiForgeryToken"]/@value').get()
        yield scrapy.FormRequest(
            url=f"https://www.newyorkpizza.{top_level_domain}/General/GetFilteredStores/",
            formdata={"includeSliceStores": "false", "storeIds": ""},
            headers={"RequestVerificationToken": auth_token},
            callback=self.parse,
            cb_kwargs={"top_level_domain": top_level_domain},
        )

    def parse(self, response, top_level_domain=None, **kwargs):
        for store in response.json():
            item = DictParser.parse(store)
            if item["name"].startswith("New York Pizza "):
                item["branch"] = item["name"].lstrip("New York Pizza ")
                item["name"] = "New York Pizza"
            item["ref"] = f"{top_level_domain}-{item['ref']}"
            item["postcode"], item["city"] = store["address_line_2"].split(maxsplit=1)
            item["country"] = top_level_domain.upper()
            item["website"] = response.urljoin(store["details_url"])
            item["opening_hours"] = self.convert_opening_hours(store, top_level_domain)
            if item["name"] != "S4D Test":
                yield item

    @staticmethod
    def convert_opening_hours(store, language):
        days_to_en = DAYS_DE if language == "de" else DAYS_EN
        re_interval = re.compile(r"(\d\d:\d\d) - (\d\d:\d\d)")
        hours = OpeningHours()
        for entry in store["opening_hours"]:
            for weekday in entry["key"].split("-"):
                for open_time, close_time in re_interval.findall(entry["value"]):
                    hours.add_range(days_to_en[weekday], open_time, close_time)
        return hours
