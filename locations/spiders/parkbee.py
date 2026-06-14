from datetime import datetime, timedelta, timezone
from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.items import Feature


class ParkbeeSpider(Spider):
    name = "parkbee"
    item_attributes = {"brand": "ParkBee", "brand_wikidata": "Q121536325"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        # Force the search to next Wednesday at 12:00 PM UTC to ensure max availability
        # and to bypass night/weekend closures
        now = datetime.now(timezone.utc)
        target_date = (now + timedelta(days=7 - (now.weekday() - 2) % 7)).replace(
            hour=12, minute=0, second=0, microsecond=0
        )
        start_t = target_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_t = (target_date + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Radius 24 is the closest ISEADGG radius to the 25km search radius
        for lat, lon in country_iseadgg_centroids(["NL", "BE", "GB"], 24):
            yield JsonRequest(
                url="https://maps-api.parkbee.net/v1/garages/search",
                data={
                    "latitude": str(lat),
                    "longitude": str(lon),
                    "searchRadius": "25",
                    "product": "go",
                    "startTime": start_t,
                    "endTime": end_t,
                },
                headers={"Origin": "https://maps-web.parkbee.com"},
                callback=self.parse,
            )

    def parse(self, response: Response) -> Iterable[Feature]:
        for garage in response.json():
            if garage.get("isSuspended"):
                continue

            # the API returns "state": "None"
            garage.pop("state", None)

            item = DictParser.parse(garage)
            item["ref"] = garage.get("garageId")

            apply_category(Categories.PARKING, item)
            item["extras"]["fee"] = "yes"
            item["extras"]["access"] = "customers"

            if garage.get("isOutdoor"):
                item["extras"]["parking"] = "surface"

            if garage.get("maximumHeadSpaceInMeters"):
                item["extras"]["maxheight"] = garage["maximumHeadSpaceInMeters"]
            if garage.get("widthRestrictionInMeters"):
                item["extras"]["maxwidth"] = garage["widthRestrictionInMeters"]

            if (
                capacity := (garage.get("garageComprehensiveInfo") or {})
                .get("availability", {})
                .get("currentTotalCapacity")
            ):
                item["extras"]["capacity"] = capacity

            apply_yes_no("wheelchair", item, garage.get("wheelChairAccessible"))
            apply_yes_no(Fuel.ELECTRIC, item, garage.get("evCharging"))
            apply_yes_no("supervised", item, garage.get("manned"))
            apply_yes_no("surveillance", item, garage.get("closedCircuitTelevision"))

            yield item
