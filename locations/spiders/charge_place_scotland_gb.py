from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class ChargePlaceScotlandGBSpider(Spider):
    name = "charge_place_scotland_gb"
    item_attributes = {"brand": "ChargePlace Scotland", "brand_wikidata": "Q105359316"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield JsonRequest(
            url="https://account.chargeplacescotland.org/api/v3/poi/chargepoint/static",
            headers={"api-auth": "c3VwcG9ydCtjcHNhcGlAc3dhcmNvLmNvbTpreWJUWCZGTyQhM3FQTnlhMVgj"},
        )

    def parse(self, response, **kwargs):
        for location in response.json()["features"]:
            item = DictParser.parse(location["properties"])
            # Yep this is GeoJson, yep they have it the wrong way around
            item["lat"], item["lon"] = location["geometry"]["coordinates"]
            item["name"] = location["properties"]["address"]["sitename"]
            item["image"] = location["properties"]["imageUrl"]
            item["website"] = f'https://chargeplacescotland.org/cpmap/chargepoint/{item["ref"]}/'
            # TODO: connectors available location["properties"]["connectorGroups"]
            apply_category(Categories.CHARGING_STATION, item)
            yield item
