from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES

PREEM = {"brand": "Preem", "brand_wikidata": "Q598835"}
UNOX = {"brand": "Uno-X", "brand_wikidata": "Q3362746"}
YX = {"brand": "YX", "brand_wikidata": "Q4580519"}


class YxSpider(Spider):
    name = "yx"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.preem.no/api/Stations/AllStations?$select=Id,Name,Address,PostalCode,City,PhoneNumber,StationType,StationSort,StationCardImage,OpeningHourWeekdayTime,ClosingHourWeekdayTime,OpeningHourSaturdayTime,ClosingHourSaturdayTime,OpeningHourSundayTime,ClosingHourSundayTime,CoordinateLatitude,CoordinateLongitude,Services/Name,Services/LinkedPage,Services/IconCssClass,FuelTypes/Name,FuelTypes/LinkedPage,FuelTypes/IconCssClass,FuelTypes/TextColor,FuelTypes/BackgroundColor,FuelTypes/BorderColor,FuelTypes/Type,FriendlyUrl,CampaignImage,CampaignUrl,TrailerRentalUrl,IsTrb,IsSaifa,IsSaifaStation,IsUnoX,IsUnoXTruck,TillhorInternationellaAllianser&$expand=FuelTypes,Services&currentLanguage=no",
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["FriendlyUrl"]
            item["lat"] = location["CoordinateLatitude"]
            item["lon"] = location["CoordinateLongitude"]
            item["street_address"] = item.pop("addr_full")
            if "https:" not in location["FriendlyUrl"]:
                item["website"] = "https://www.preem.no" + location["FriendlyUrl"]
            else:
                item["website"] = item["ref"]
            if "Yx" in item["name"] and "7-eleven" not in item["name"]:
                item.update(YX)
                item["branch"] = item.pop("name").removeprefix("Yx ")
                apply_category(Categories.FUEL_STATION, item)
            elif "Uno-x" in item["name"] and "7-eleven" not in item["name"]:
                item.update(UNOX)
                item["branch"] = item.pop("name").removeprefix("Uno-x ")
                apply_category(Categories.FUEL_STATION, item)
            elif "7-eleven" in item["name"]:
                item.update(SEVEN_ELEVEN_SHARED_ATTRIBUTES)
                item["branch"] = item.pop("name").removeprefix("Yx ").removeprefix("7-eleven ")
                apply_category(Categories.SHOP_CONVENIENCE, item)
            else:
                item.update(PREEM)
                item["name"] = None
                apply_category(Categories.FUEL_STATION, item)

            for fuel_type in location["FuelTypes"]:
                apply_yes_no(Fuel.ADBLUE, item, "adblue" in fuel_type["Name"].lower())
                apply_yes_no(Fuel.DIESEL, item, "diesel" in fuel_type["Name"].lower())
                apply_yes_no(Fuel.OCTANE_95, item, "bensin 95" in fuel_type["Name"].lower())
                apply_yes_no(Fuel.OCTANE_98, item, "bensin 98" in fuel_type["Name"].lower())
                apply_yes_no(Fuel.BIODIESEL, item, "hvo100" in fuel_type["Name"].lower())
            yield item
