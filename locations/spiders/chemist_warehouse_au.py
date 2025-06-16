from typing import Any, Iterable

from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.pipelines.address_clean_up import merge_address_lines


class ChemistWarehouseAUSpider(Spider):
    name = "chemist_warehouse_au"
    item_attributes = {"brand": "Chemist Warehouse", "brand_wikidata": "Q48782120"}

    def make_request(self, lat: float, lon: float, offset: int, limit: int = 100) -> JsonRequest:
        return JsonRequest(
            url=f"https://api.chemistwarehouse.com.au/web/v1/channels/cwr-cw-au/en/radius?channel-type=store&latitude={lat}&longitude={lon}&search-type=store-locator&offset={offset}&limit={limit}",
            cb_kwargs=dict(lat=lat, lon=lon, offset=offset, limit=limit),
        )

    def start_requests(self) -> Iterable[JsonRequest]:
        for city in city_locations("AU", 15000):
            yield self.make_request(city["latitude"], city["longitude"], 0)

    def parse(self, response: Response, lat: float, lon: float, offset: int, limit: int) -> Any:
        locations = response.json().get("channels", [])
        for location in locations:
            location_info = location.get("channel", {})
            location_info.update(location_info.pop("address", {}))
            location_info["street-address"] = merge_address_lines(
                [location_info.pop("streetNumber", ""), location_info.pop("streetName", "")]
            )
            item = DictParser.parse(location_info)
            item["ref"] = location_info.get("key")
            item["extras"]["fax"] = location_info.get("fax")
            yield item
        if len(locations) == limit:
            yield self.make_request(lat, lon, offset + limit)
