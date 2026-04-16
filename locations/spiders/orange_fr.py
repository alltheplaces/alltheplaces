from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class OrangeFRSpider(Spider):
    name = "orange_fr"
    item_attributes = {"brand": "Orange", "brand_wikidata": "Q1431486"}
    skip_auto_cc_domain = True
    skip_auto_cc_spider_name = True

    def make_request(self, page: int, page_size: int = 100) -> JsonRequest:
        return JsonRequest(
            url="https://7jl9sk5vbq-dsn.algolia.net/1/indexes/stores_locator_ofr/query?x-algolia-application-id=7JL9SK5VBQ&x-algolia-api-key=b2b7037d97e57d65b53dc5daab37b989",
            data={"params": "hitsPerPage={}&page={}".format(page_size, page)},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for location in data["hits"]:
            if location["Status"] != "ACTIVE":
                continue
            item = Feature()
            item["ref"] = location["objectID"]
            item["branch"] = location["Location name"].removeprefix("Orange").strip(" -")
            item["lat"] = location["_geoloc"]["lat"]
            item["lon"] = location["_geoloc"]["lng"]
            item["website"] = urljoin("https://agence.orange.fr/", location["URL"])
            item["phone"] = location["Phone"]
            item["street_address"] = location["Address 1"]
            item["postcode"] = location["Postal Code"]
            item["city"] = location["City"]

            item["opening_hours"] = OpeningHours()
            for day, times in location["horaires"].items():
                for time in times:
                    item["opening_hours"].add_range(day, time[0], time[1])

            apply_category(Categories.SHOP_TELECOMMUNICATION, item)

            yield item

        if data["page"] < data["nbPages"]:
            yield self.make_request(data["page"] + 1, data["hitsPerPage"])
