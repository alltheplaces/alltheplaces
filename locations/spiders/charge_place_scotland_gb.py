import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import apply_category
from locations.dict_parser import DictParser


class ChargePlaceScotlandGBSpider(Spider):
    name = "charge_place_scotland_gb"
    item_attributes = {"brand": "ChargePlace Scotland", "brand_wikidata": "Q105359316"}
    start_urls = ["https://chargeplacescotland.org/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = re.search(r"apiAuthKey: '(\w+)',", response.text).group(1)
        yield JsonRequest(
            url="https://account.chargeplacescotland.org/api/v3/poi/chargepoint/static",
            headers={"api-auth": token},
            callback=self.parse_api,
        )

    def parse_api(self, response, **kwargs):
        for location in response.json()["features"]:
            item = DictParser.parse(location["properties"])
            # Yep this is GeoJson, yep they have it the wrong way around
            item["lat"], item["lon"] = location["geometry"]["coordinates"]
            item["name"] = location["properties"]["address"]["sitename"]
            item["image"] = location["properties"]["imageUrl"]
            item["website"] = f'https://chargeplacescotland.org/cpmap/chargepoint/{item["ref"]}/'
            if location["properties"]["tariff"]["amount"] and location["properties"]["tariff"]["currency"]:
                item["extras"]["charge"] = "{} {}/kWh".format(
                    location["properties"]["tariff"]["amount"], location["properties"]["tariff"]["currency"]
                )
            # TODO: connectors available location["properties"]["connectorGroups"]

            apply_category({"man_made": "charge_point"}, item)

            yield item
