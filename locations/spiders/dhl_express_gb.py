from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.dhl_express_de import DHL_EXPRESS_SHARED_ATTRIBUTES


class DhlExpressGBSpider(Spider):
    name = "dhl_express_gb"
    item_attributes = DHL_EXPRESS_SHARED_ATTRIBUTES
    allowed_domains = ["track.dhlecommerce.co.uk"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://track.dhlecommerce.co.uk/UKMail/Handlers/DepotData", method="POST")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location.update(location.pop("DepotAddress", {}))
            item = DictParser.parse(location)

            item["ref"] = location.get("DepotNumber")
            item["name"] = location.get("DepotName")
            item["street_address"] = merge_address_lines(
                [location["Address1"], location["Address2"], location["Address3"]]
            )
            item["city"] = location.get("PostalTown")
            item["lat"] = location.get("Latitude")
            item["lon"] = location.get("Longitude")
            item["phone"] = location.get("Telephone")

            oh = OpeningHours()
            for day in location.get("OpeningTimes"):
                oh.add_range(
                    day=DAYS[day.get("Day") - 1], open_time=day.get("OpenTime"), close_time=day.get("CloseTime")
                )
            item["opening_hours"] = oh

            apply_category(Categories.POST_DEPOT, item)

            yield item
