from typing import AsyncIterator

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.http import Request

from locations.items import Feature


class UsArmyNationalGuardSpider(Spider):
    name = "us_army_national_guard"
    item_attributes = {
        "brand": "US Army National Guard",
        "brand_wikidata": "Q928670",
        "country": "US",
    }
    allowed_domains = ["nationalguard.com"]

    async def start(self) -> AsyncIterator[Request]:
        for state in GeonamesCache().get_us_states().keys() | ["USPR", "USGU", "USVI"]:
            yield Request(url="https://nationalguard.com/api/state/" + state)

    def parse(self, response, **kwargs):
        data = response.json()
        for row in data["locations"]:
            properties = {
                "name": row["name"],
                "ref": row["id"],
                "addr_full": row["address"],
                "state": row["state"],
                "phone": row["phone"],
                "lat": row["latitude"],
                "lon": row["longitude"],
            }
            yield Feature(**properties)
