from typing import Any, AsyncIterator

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class SouthernRailwayGBSpider(Spider):
    name = "southern_railway_gb"
    item_attributes = {"operator": "Southern Railway", "operator_wikidata": "Q1258373"}

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            "https://www.southernrailway.com/travel-information/station-information",
            headers={"User-Agent": BROWSER_DEFAULT},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for link in response.xpath('//a[contains(@href, "/travel-information/station-information/")]/@href').getall():
            website = response.urljoin(link)
            yield FormRequest(
                "https://stationpages.fabdigital.uk/api/index.php?api_public/get_station_data",
                formdata={"page": "api_public", "action": "get_station_data", "crs": website.split("/")[5]},
                callback=self.parse_station,
                cb_kwargs={"website": website},
            )

    def parse_station(self, response: Response, **kwargs: Any) -> Any:
        station = response.json()["response"]["stationData"]

        if station["stationInfo"]["stationOperatorCode"] != "SN":
            return

        item = Feature()
        item["ref"] = station["stationInfo"]["crs"]
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
