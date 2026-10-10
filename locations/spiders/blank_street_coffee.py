import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours

IMAGE_BASE_URL = "https://res.cloudinary.com/blank-street/image/upload"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", "and")).strip("-")


class BlankStreetCoffeeSpider(Spider):
    name = "blank_street_coffee"
    item_attributes = {"brand": "Blank Street Coffee", "brand_wikidata": "Q114792509"}
    start_urls = ["https://www.blankstreet.com/en-GB/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        page_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for location in page_data["props"]["pageProps"]["carts"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["country"] = "GB" if location["geoName"] == "uk" else location["geoName"].upper()
            item["website"] = "https://www.blankstreet.com/locations/{}/{}-{}".format(
                location["marketName"], location["id"], slugify(location["name"])
            )
            if relative_path := (location.get("imgUrl") or {}).get("relativePath"):
                item["image"] = IMAGE_BASE_URL + relative_path.split("?")[0]
            item["opening_hours"] = OpeningHours()
            for day, hours in (location.get("openingHoursSystem") or {}).items():
                if hours:
                    item["opening_hours"].add_range(day, hours["open"][:5], hours["close"][:5])
            apply_category(Categories.COFFEE_SHOP, item)
            yield item
