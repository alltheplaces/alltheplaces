import json
from typing import AsyncIterator

from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class BeevGBSpider(PlaywrightSpider):
    name = "beev_gb"
    item_attributes = {"brand": "Be.EV", "brand_wikidata": "Q118263083"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://be-ev.co.uk/api/sites/GetMarkersWithFilters?Availability=o:0,a:0,&ChargerType=f:0,r:0,ur:0&ConnectorType=type2:0,ccs:0,chademo:0&Facilities=RESTAURANT:0,PARKING_LOT:0,SPORT:0,CAFE:0,HOTEL:0,MALL:0,SUPERMARKET:0,TRAIN_STATION:0,RECREATION_AREA:0,NATURE:0&source=fuuse",
        )

    def parse(self, response, **kwargs):
        for location in json.loads(response.xpath("//pre//text()").get()):
            if location["status"] == 4:
                continue  # Upcoming

            item = Feature()
            item["ref"] = location["siteId"]
            item["lat"] = location["coordinates"]["lat"]
            item["lon"] = location["coordinates"]["long"]
            item["name"] = location["name"]
            item["postcode"] = location["formattedAddress"]["postCode"]

            apply_yes_no(Extras.FEE, item, location["tariff"]["amount"] == "0.00", False)
            item["extras"]["charge"] = "{} {}/kWh".format(location["tariff"]["amount"], location["tariff"]["currency"])

            apply_category(Categories.CHARGING_STATION, item)

            yield item
