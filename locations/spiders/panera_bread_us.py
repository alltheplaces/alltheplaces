import re

from geonamescache import GeonamesCache
from scrapy import Request, Spider

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser


def slugify(s):
    return re.sub(r"\W+", "-", s).lower()


class PaneraBreadUSSpider(Spider):
    name = "panera_bread_us"
    item_attributes = {"brand": "Panera Bread", "brand_wikidata": "Q7130852"}

    def start_requests(self):
        for state in GeonamesCache().get_us_states():
            yield Request(
                f"https://www-api.panerabread.com/www-api/public/cafe/location/{state.lower()}",
                headers={"Referer": "https://www.panerabread.com/"},
            )

    def parse(self, response):
        for city in response.json():
            for cafe in city["cafes"]:
                item = DictParser.parse(cafe)
                item["branch"] = item.pop("name")
                item["ref"] = cafe["cafeId"]
                item["street_address"] = item.pop("street")
                item["website"] = (
                    f"https://www.panerabread.com/content/panerabread_com/en-us/cafe/locations/{slugify(cafe['state'])}/{slugify(cafe['city'])}/{slugify(cafe['streetName'])}"
                )

                features = cafe["searchFlags"]
                apply_yes_no(Extras.INDOOR_SEATING, item, features["hasDineIn"])
                apply_yes_no(Extras.DELIVERY, item, features["hasDelivery"])
                apply_yes_no(Extras.TAKEAWAY, item, features["hasPickup"])
                apply_yes_no(Extras.DRIVE_THROUGH, item, features["hasDriveThru"])

                yield item
