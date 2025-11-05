from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.spiders.dhl_express_de import DHL_EXPRESS_SHARED_ATTRIBUTES


class DhlExpressGBSpider(Spider):
    name = "dhl_express_gb"
    item_attributes = DHL_EXPRESS_SHARED_ATTRIBUTES
    allowed_domains = ["dhlparcel.co.uk"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://track.dhlparcel.co.uk/UKMail/Handlers/DepotData", method="POST")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for data in response.json():
            item = Feature()
            item["ref"] = data.get("DepotNumber")
            item["name"] = data.get("DepotName")
            item["postcode"] = data.get("DepotAddress", {}).get("Postcode")
            item["country"] = data.get("DepotAddress", {}).get("Country")
            item["city"] = data.get("DepotAddress", {}).get("PostalTown")
            item["street_address"] = data.get("DepotAddress", {}).get("Address1")
            item["lat"] = data.get("Latitude")
            item["lon"] = data.get("Longitude")
            item["phone"] = data.get("Telephone")

            oh = OpeningHours()
            for day in data.get("OpeningTimes"):
                oh.add_range(
                    day=DAYS[day.get("Day") - 1], open_time=day.get("OpenTime"), close_time=day.get("CloseTime")
                )
            item["opening_hours"] = oh

            apply_category(Categories.POST_DEPOT, item)

            yield item
