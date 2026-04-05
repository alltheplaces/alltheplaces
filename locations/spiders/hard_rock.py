from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class HardRockSpider(Spider):
    name = "hard_rock"
    allowed_domains = ["www.hardrock.com"]
    start_urls = [
        "https://www.hardrock.com/graphql/execute.json/shrss/locationListing;cfPath=/content/dam/shrss/cf/locations;hotel=Hotel;cafe=Cafe;casino=Casino"
    ]

    cats = {
        "Cafe": ({"brand": "Hard Rock Cafe", "brand_wikidata": "Q918151"}, Categories.RESTAURANT),
        "Hotel": ({"brand": "Hard Rock Hotel", "brand_wikidata": "Q109275902"}, Categories.HOTEL),
        "Live": ({"brand": "Hard Rock Live", "brand_wikidata": "Q5655372"}, Categories.MUSIC_VENUE),
        "Hotel & Casino": ({"brand": "Hard Rock Hotel & Casino"}, Categories.HOTEL),
        "Casino": ({"brand": "Hard Rock Casino"}, Categories.CASINO),
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["locationsList"]["items"]:
            item = DictParser.parse(location)

            item["website"] = location.get("webpage")
            item["name"] = location.get("locationShortName")

            if category := self.cats.get(location.get("lineOfBusiness")):
                item.update(category[0])
                apply_category(category[1], item)
            else:
                self.logger.error("Unexpected type: {}".format(location.get("lineOfBusiness")))
            yield item
