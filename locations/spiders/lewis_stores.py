from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours


class LewisStoresSpider(Spider):
    name = "lewis_stores"
    item_attributes = {"brand": "Lewis Stores", "brand_wikidata": "Q115117217"}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://lewisstores.co.za/controllers/get_locations.php",
            formdata={"param1": "Lewis Stores"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if "CLOSED" in location["StoreLocatorName"]:
                continue

            location["Phone"] = "; ".join([location["Phone"], location.pop("Phone2"), location.pop("Phone3")])

            item = DictParser.parse(location)
            country_code_mapping = {
                182: "NA",
                73: "ZA",
                219: "SZ",
                155: "LS",
                101: "BW",
            }
            item["branch"] = location["StoreLocatorName"]
            item["email"] = item["email"].replace("NULL", "")
            item["country"] = country_code_mapping[location["CountryId"]]

            if item["country"] != "ZA" and item["postcode"] in ["9000", "9999"]:
                item.pop("postcode")

            oh = OpeningHours()
            time_format = "%I:%M%p" if "am" in location["TradingMonFri"] else "%H:%M"

            for days, trading in [
                (DAYS_WEEKDAY, location["TradingMonFri"]),
                (["Sat"], location["TradingSat"]),
                (["Sun"], location["TradingSunPub"]),
            ]:
                if not trading:
                    continue
                if trading.lower() in ["closed", "no"]:
                    oh.set_closed(days)
                else:
                    open_time, close_time = trading.replace("h", ":").split("-")
                    oh.add_days_range(days, open_time.strip(), close_time.strip(), time_format)

            item["opening_hours"] = oh

            yield item
