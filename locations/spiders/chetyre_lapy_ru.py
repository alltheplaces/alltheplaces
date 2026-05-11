import json
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class ChetyreLapyRUSpider(scrapy.Spider):
    name = "chetyre_lapy_ru"
    allowed_domains = ["4lapy.ru"]
    start_urls = ["https://4lapy.ru/shops/"]
    item_attributes = {"brand_wikidata": "Q62390783"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = "RU"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        next_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        if not next_data:
            self.logger.error(f"Could not find __NEXT_DATA__ script on {response.url}.")
            return

        yield JsonRequest(
            url=f"https://4lapy.ru/_next/data/{next_data['buildId']}/shops.json",
            callback=self.parse_pois,
        )

    def parse_pois(self, response):
        for poi in list(response.json()["pageProps"]["fallback"].values())[0]["items"]:
            item = Feature()
            item["ref"] = poi["id"]
            item["addr_full"] = poi["address"]
            item["city"] = poi["cityName"]
            item["lat"] = poi["coordinates"]["lat"]
            item["lon"] = poi["coordinates"]["lon"]
            item["image"] = poi["photo"]
            item["website"] = "https://4lapy.ru/shops/{}/".format(item["ref"].lower())

            item["opening_hours"] = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                item["opening_hours"].add_range(
                    day, poi["scheduleFull"]["{}TO".format(day)], poi["scheduleFull"]["{}TC".format(day)], "%H%M%S"
                )

            yield item
