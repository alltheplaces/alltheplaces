import re
from typing import Any, Iterable

from scrapy import FormRequest, Request
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class GoOutdoorsGBSpider(Spider):
    name = "go_outdoors_gb"
    item_attributes = {"brand": "Go Outdoors", "brand_wikidata": "Q75293941"}

    def start_requests(self) -> Iterable[Request]:
        yield FormRequest(
            url="https://www.gooutdoors.co.uk/google/store-locator",
            formdata={
                "postcode": "",
                "submit": "Find+stores",
                "submit": "1",
                "radius": "500",
                "ac_store_limit": "300",
                "current_view": "list",
                "fascias%5B%5D": "GO",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        coords_map = {}
        for lat, lon, ref in re.findall(
            r"LatLng\((-?\d+\.\d+), (-?\d+\.\d+)\);.+?markers\[(\d+)]", response.text, re.DOTALL
        ):
            coords_map[ref] = (lat, lon)

        for location in response.xpath("//li[@data-id]"):
            item = Feature()
            item["ref"] = location.xpath("@data-id").get()
            item["lat"], item["lon"] = coords_map.get(item["ref"], (None, None))
            item["name"] = location.xpath(".//h3/a/text()").get()
            item["street_address"] = location.xpath('.//p[@class="storeAddress"][1]/text()').get()
            item["postcode"] = location.xpath('.//p[@class="storeAddress"][2]/text()').get()
            extract_phone(item, location)
            item["website"] = response.urljoin(location.xpath('.//a[text()="View store details"]/@href').get())

            item["opening_hours"] = OpeningHours()
            for rule in location.xpath(".//tr/td/text()").getall():
                day, times = rule.split(" ", 1)
                start_time, end_time = times.split(" - ")
                item["opening_hours"].add_range(day, start_time, end_time, "%H%M")

            yield item
