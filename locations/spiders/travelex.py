from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser


class TravelexSpider(Spider):
    name = "travelex"
    item_attributes = {"brand": "Travelex", "brand_wikidata": "Q2337964"}
    countries = [
        "ae",
        "au",
        "nlbe",
        "enbh",
        "enca",
        "ench",
        "encn",
        "cz",
        "de",
        "fr",
        "gb",
        "enhk",
        "in",
        "itit",
        "enjp",
        "mo",
        "my",
        "nl",
        "nm",
        "nz",
        "om",
        "qa",
        "uk",
        "us",
        "za",
    ]

    website_map = {
        "au": "https://www.travelex.com.au/stores/{}",
        "gb": "https://www.travelex.co.uk/stores/{}",
    }

    # API documentation
    # https://api.travelex.net/docs/api/index.html#api-store-getStoreAll
    #
    # Countries check
    # If a new country is added to the brand, you might want to check them here:
    # https://api.travelex.net/salt/site/list?key=Travelex

    async def start(self) -> AsyncIterator[Request]:
        for country in self.countries:
            yield Request(
                f"https://api.travelex.net/salt/store/search?key=Travelex&mode=storeLocator&site=/{country}&lat={0.0}&lng={0.0}",
                meta={"country": country},
            )

    def parse(self, response):
        data = response.json()
        item_categories = data.get("items")
        for category in item_categories:
            stores = category.get("stores")
            for row in stores:
                item = DictParser.parse(row)
                item["branch"] = item.pop("name")
                item["addr_full"] = row.get("formattedAddress")
                item["extras"] = {
                    "directions": row.get("directions"),
                    "notes": row.get("notes"),
                    "terminal": row.get("terminal"),
                }

                if url_format := self.website_map.get(response.meta["country"]):
                    item["website"] = url_format.format(row["storeUrl"])
                else:
                    item["website"] = None

                yield item
