from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class ShelterGBSpider(Spider):
    name = "shelter_gb"
    item_attributes = {"brand": "Shelter", "brand_wikidata": "Q7493943"}
    start_urls = [
        "https://england.shelter.org.uk/page-data/sq/d/251240610.json",
        "https://scotland.shelter.org.uk/page-data/sq/d/251240610.json",
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for shop in response.json()["data"]["allContentfulPageShop"]["nodes"]:
            shop.update(shop.pop("shop"))
            shop.update(shop.pop("location"))
            item = DictParser.parse(shop)
            if "Scotland" in shop["region"]:
                country = "scotland"
            else:
                country = "england"
            item["ref"] = item["website"] = "https://{}.shelter.org.uk{}".format(country, shop["navigation"]["path"])
            item["name"] = shop["shopName"]
            item["addr_full"] = shop["shortAddress"]
            yield item
