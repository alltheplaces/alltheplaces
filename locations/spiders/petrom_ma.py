from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class PetromMASpider(Spider):
    name = "petrom_ma"
    item_attributes = {"brand_wikidata": "Q110028558"}
    start_urls = ["http://petrom.ma/get-stations/?action=reseau"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for row in response.text.split("!"):
            if not row:
                continue
            city, _, _, lon, lat = row.split(";;")
            item = Feature()
            item["lat"] = lat
            item["lon"] = lon
            item["city"] = city.strip()

            apply_category(Categories.FUEL_STATION, item)

            yield item
