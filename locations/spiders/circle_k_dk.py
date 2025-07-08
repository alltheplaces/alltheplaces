import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CircleKDKSpider(scrapy.Spider):
    name = "circle_k_dk"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    start_urls = ["https://www.circlek.dk/station-search"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for station in json.loads(response.xpath('//*[@type="application/json"]/text()').get())["ck_sim_search"][
            "station_results"
        ].values():
            if station["/sites/{siteId}"]["brand"] == "CIRCLEK":
                station.update(station["/sites/{siteId}/addresses"].pop("PHYSICAL"))
                station.update(station.pop("/sites/{siteId}/location"))
                station.update(station.pop("/sites/{siteId}"))
                item = DictParser.parse(station)
                item["branch"] = item.pop("name").removeprefix("CIRCLE K ")
                item["email"] = station["/sites/{siteId}/contact-details"]["emails"]["DN"][0]
                item["phone"] = station["/sites/{siteId}/contact-details"]["phones"]["WOR"]
                apply_category(Categories.FUEL_STATION, item)
                yield item
