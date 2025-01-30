import re
from typing import Any, Iterable

import chompjs
import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day, DAYS_FR


class CasinoFRSpider(scrapy.Spider):
    name = "casino_fr"
    item_attributes = {"brand_wikidata": "Q89029184"}

    def start_requests(self) -> Iterable[Request]:
        yield scrapy.Request(url="https://petitcasino.casino.fr/api/store", callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for casino in response.json()["stores"]:
            if casino["g"] == 30843:
                yield scrapy.Request(
                    url="https://petitcasino.casino.fr/fr/stores/" + casino["storeId"],
                    cb_kwargs={"lat": casino["lat"], "lon": casino["lng"]},
                    callback=self.parse_details,
                )

    def parse_details(self, response, **kwargs):
        raw_data = chompjs.parse_js_object(
            re.search(
                r"store:({.*}),storesAround", response.xpath('//script[contains(text(),"store")]/text()').get()
            ).group(1)
        )
        item = DictParser.parse(raw_data)
        item["lat"] = kwargs["lat"]
        item["lon"] = kwargs["lon"]
        item["website"] = response.url
        apply_category(Categories.SHOP_SUPERMARKET, item)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class="col-span-1 space-y-4"]/*[@class="flex justify-between text-h5"]'):
            day = sanitise_day(day_time.xpath("./p/text()").get().strip(), DAYS_FR)
            time = day_time.xpath("./p[2]/text()").get().strip()
            if time == "Fermé":
                item["opening_hours"].set_closed(day)
            elif "/" in time:
                for open_close_time in time.split("/"):
                    open_time, close_time = open_close_time.split("-")
                    item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
            else:
                open_time, close_time = time.split("-")
                item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())

        yield item
