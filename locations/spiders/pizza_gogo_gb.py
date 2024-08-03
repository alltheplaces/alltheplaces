from typing import Any

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaGogoGBSpider(Spider):
    name = "pizza_gogo_gb"
    item_attributes = {"brand": "Pizza GoGo", "brand_wikidata": "Q118121277"}
    start_urls = ["https://www.pizzagogo.co.uk/ajax/?do=all_stores_for_map"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in zip(
            response.json()["lat_arr"].split("|"),
            response.json()["lng_arr"].split("|"),
            response.json()["stores"].split("|"),
            response.json()["store_ids"].split("|"),
            response.json()["address_arr"].split("|"),
            response.json()["phone_arr"].split("|"),
        ):
            item = Feature()
            item["lat"], item["lon"], item["branch"], item["ref"], item["addr_full"], item["phone"] = location

            item["addr_full"] = merge_address_lines(Selector(text=item["addr_full"]).xpath("//text()").getall())
            item["website"] = "https://www.pizzagogo.co.uk/gotostore/{}".format(item["ref"])
            yield item
