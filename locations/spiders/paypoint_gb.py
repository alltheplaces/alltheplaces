from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations


class PaypointGBSpider(Spider):
    name = "paypoint_gb"
    item_attributes = {"brand": "PayPoint", "brand_wikidata": "Q7156561"}
    custom_settings = {"CONCURRENT_REQUESTS": 1, "DOWNLOAD_TIMEOUT": 120}

    def start_requests(self) -> Iterable[JsonRequest]:
        for city in city_locations("GB", 15000):
            yield JsonRequest(
                url="https://www.paypoint.com/umbraco/surface/StoreLocatorSurface/StoreLocator",
                data={
                    "searchCriteria": f'{city["latitude"]},{city["longitude"]}',
                    "product": "ATM",
                    "siteServices": "ATM",
                    "searchType": 6,
                },
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        if locations := response.json().get("ppGroups"):
            for location in locations:
                item = DictParser.parse(location)
                item["ref"] = location.get("SiteNumber")
                item["name"] = "PayPoint"
                item["located_in"] = location.get("SiteName")
                item["street_address"] = item.pop("addr_full", "")
                services = [service.get("ServiceName").strip() for service in location.get("Services")]
                # products = location.get("OtherProducts")
                # parcel_products = location.get("ParcelProducts")
                if "ATM" in services:
                    apply_category(Categories.ATM, item)
                else:
                    # Not sure about other services whether location can be collected as a PayPoint branded location
                    # https://www.paypoint.com/instore-services
                    continue
                yield item
