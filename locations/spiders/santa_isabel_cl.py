import re

from scrapy import Spider
from scrapy.http import JsonRequest
from unidecode import unidecode

from locations.categories import Categories
from locations.hours import DAYS_ES, DELIMITERS_ES, OpeningHours
from locations.items import Feature


class SantaIsabelCLSpider(Spider):
    name = "santa_isabel_cl"
    item_attributes = {
        "brand": "Santa Isabel",
        "brand_wikidata": "Q7419620",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["assets.santaisabel.cl"]
    start_urls = ["https://assets.santaisabel.cl/json/cms/page-1506.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["acf"]["localities"]:
            properties = {
                "ref": unidecode(location.get("name").lower()).replace(" ", "-"),
                "name": location.get("name"),
                "street_address": location.get("address"),
                "city": location.get("cities"),
                "state": location.get("regions"),
            }

            coordinates = re.findall(r"-?\d+\.\d*", location.get("geolocation"))
            if len(coordinates) == 2:
                properties["lat"] = coordinates[0]
                properties["lon"] = coordinates[1]

            hours_string = (
                re.sub(
                    r"\s+",
                    " ",
                    location.get("schedule").replace("<br />", " ").replace("<b>", " ").replace("</b>", " "),
                )
                .replace("Sábados, Domingos y Festivos", "Sábados a Domingos")
                .replace("Domingos y Festivos", "Domingos")
                .strip()
            )
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_ES, delimiters=DELIMITERS_ES)

            yield Feature(**properties)
