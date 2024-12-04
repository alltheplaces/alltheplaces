from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.google_url import url_to_coords


class AuchanHUSpider(Spider):
    name = "auchan_hu"
    item_attributes = {"brand": "Auchan", "brand_wikidata": "Q758603"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(url="https://auchan.hu/api/v2/cache/petrol/list")
        yield JsonRequest(url="https://auchan.hu/api/v2/cache/store/list")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["lat"], item["lon"] = url_to_coords(location["googleMapsLink"])

            if response.url == "https://auchan.hu/api/v2/cache/petrol/list":
                item["branch"] = item.pop("name").removeprefix("MH Auchan ").removesuffix(" benzinkút")
                item["name"] = "Auchan"
                item["website"] = urljoin("https://auchan.hu/petrol/", location["slug"])
                apply_category(Categories.FUEL_STATION, item)
                item["nsi_id"] = "N/A"
            else:
                item["branch"] = item.pop("name").removeprefix("Auchan ")
                item["website"] = urljoin("https://auchan.hu/stores/", location["slug"])
                apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
