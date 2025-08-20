import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class NahkaufDESpider(scrapy.Spider):
    name = "nahkauf_de"
    item_attributes = {"brand": "Nahkauf", "brand_wikidata": "Q57515238"}
    start_urls = ["https://www.nahkauf.de/"]

    def parse(self, response):
        token = re.search(
            r"accessToken:\s*\"(\w+)\",", response.xpath('//*[contains(text(),"accessToken")]/text()').get()
        ).group(1)
        yield scrapy.Request(
            url="https://api.storyblok.com/v2/cdn/stories?starts_with=import-objects%2Fmarkets&per_page=100&page=1&token={}".format(
                token
            ),
            cb_kwargs={"page": 1, "token": token},
            callback=self.parse_details,
        )

    def parse_details(self, response, **kwargs):
        if data := response.json()["stories"]:
            for store in data:
                store.update(store.pop("content"))
                item = DictParser.parse(store)
                item["branch"] = store["market_name"]
                item["street_address"] = store["street_with_house_number"]
                item["website"] = "".join(["https://www.nahkauf.de/", store.get("content_site_slug_name", "")])
                apply_category(Categories.SHOP_SUPERMARKET, item)
                item["opening_hours"] = OpeningHours()
                for day_time in store["opening_hours"]:
                    day = DAYS[int(day_time["day_of_week"]) - 1]
                    if day_time["is_closed"] is True:
                        item["opening_hours"].set_closed(day)
                    else:
                        open_time = day_time["open_from"]
                        close_time = day_time["open_to"]
                        item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)

                yield item
            next_page = kwargs["page"] + 1
            yield scrapy.Request(
                url="https://api.storyblok.com/v2/cdn/stories?starts_with=import-objects%2Fmarkets&per_page=100&page={}&token={}".format(
                    next_page, kwargs["token"]
                ),
                cb_kwargs={"page": next_page, "token": kwargs["token"]},
                callback=self.parse_details,
            )
