from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class OrlenPaczkaPLSpider(Spider):
    name = "orlen_paczka_pl"
    item_attributes = {"brand": "Orlen Paczka", "brand_wikidata": "Q110457879"}
    start_urls = ["https://ruch-osm.sysadvisors.pl/api.php"]
    allowed_domains = ["ruch-osm.sysadvisors.pl"]

    def start_requests(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                body='{"a":"f","s":0}',
                headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                method="POST",
            )

    def parse(self, response):
        for location in response.json()["pts"]:

            if location["t"] != "A" or location["r"] == "PKN":
                continue

            properties = {
                "ref": location["p"],
                "lat": location["la"],
                "lon": location["lo"],
                "street_address": location["a_al"],
                "city": location["a_c"],
                "postcode": location["a_pc"],
                "opening_hours": OpeningHours(),
            }
            properties["opening_hours"].add_ranges_from_string(location["o"], days=DAYS_PL)
            apply_category(Categories.PARCEL_LOCKER, properties)
            yield Feature(**properties)
