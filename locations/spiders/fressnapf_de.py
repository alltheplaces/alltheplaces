from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FressnapfDESpider(Spider):
    name = "fressnapf_de"
    item_attributes = {"brand": "Fressnapf", "brand_wikidata": "Q875796"}
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}
    api_key = "fressnapfDE"
    website_format = "https://www.fressnapf.de/stores/{}/"

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://api.os.fressnapf.com/rest/v2/{}/stores?fields=FULL".format(self.api_key),
            data={"radius": 20000, "filterProperties": []},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            if location["active"] is False:
                continue

            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["addr_full"] = location["address"]["formattedAddress"]
            item["state"] = location["address"].get("region", {}).get("name")
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            item["street_address"] = merge_address_lines(
                [location["address"].get("line1"), location["address"].get("line2")]
            )
            item["opening_hours"] = OpeningHours()
            for rule in location.get("openingHours", {}).get("weekDayOpeningList", []):
                if rule["closed"] is True:
                    item["opening_hours"].set_closed(rule["weekDayId"])
                else:
                    item["opening_hours"].add_range(
                        rule["weekDayId"], rule["openingTime"]["formattedHour"], rule["closingTime"]["formattedHour"]
                    )
            item["website"] = self.website_format.format(location.get("partForUrlGen") or item["ref"])

            yield from self.post_process_item(item, response, location) or []

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs):
        item["branch"] = location["displayName"].removeprefix("Fressnapf ")
        if "XXL" in item["branch"].split():
            item["name"] = "Fressnapf XXL"
            item["branch"] = item["branch"].replace("XXL", "").strip()
        yield item
