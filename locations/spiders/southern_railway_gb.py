import json
from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class SouthernRailwayGBSpider(Spider):
    name = "southern_railway_gb"
    item_attributes = {"operator": "Southern Railway", "operator_wikidata": "Q1258373"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Any]:
        yield Request("https://www.southernrailway.com/travel-information/station-information")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath('//a[contains(@href, "/travel-information/station-information/")]/@href').getall():
            website = response.urljoin(link)
            # URL is .../station-information/<CRS>/<Station-Name>, so the CRS
            # code is the second-to-last path segment.
            params = urlencode({"page": "api_public", "action": "get_station_data", "crs": website.split("/")[-2]})
            yield Request(
                f"https://stationpages.fabdigital.uk/api/index.php?api_public/get_station_data&{params}",
                callback=self.parse_station,
                cb_kwargs={"website": website},
            )

    def parse_station(self, response: Response, **kwargs: Any) -> Any:
        # The upstream API is unreliable and occasionally returns a malformed/empty
        # body. Skip those so a single bad response can't abort the whole crawl.
        try:
            station = response.json()["response"]["stationData"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return

        if station["stationInfo"]["stationOperatorCode"] != "SN":
            return

        item = Feature()
        item["ref"] = item["extras"]["ref:crs"] = station["stationInfo"]["crs"]
        item["name"] = station["stationInfo"]["name"]
        item["lat"] = station["stationInfo"]["latitude"]
        item["lon"] = station["stationInfo"]["longitude"]
        item["addr_full"] = merge_address_lines(station["stationInfo"]["address"])
        item["postcode"] = station["stationInfo"]["postCode"]
        item["website"] = kwargs["website"]

        if station["facilities"]["showFacilities"] is True:
            apply_yes_no(Extras.ATM, item, station["facilities"]["cashMachine"] is True)
            apply_yes_no(Extras.BABY_CHANGING_TABLE, item, station["facilities"]["babyChange"] is True)
            apply_yes_no(Extras.SHOWERS, item, station["facilities"]["showers"] is True)
            apply_yes_no(Extras.TOILETS, item, station["facilities"]["toilets"] is True)
            apply_yes_no(Extras.WIFI, item, station["facilities"]["wifi"] is True)

        apply_category(Categories.TRAIN_STATION, item)

        yield item
