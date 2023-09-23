from unidecode import unidecode

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category, Categories
from locations.hours import DAYS, DAYS_PL, OpeningHours
from locations.items import Feature


class InPostPLSpider(Spider):
    name = "inpost_pl"
    item_attributes = {"brand": "InPost", "brand_wikidata": "Q3182097"}
    allowed_domains = ["inpost.pl"]
    start_urls = ["https://inpost.pl/sites/default/files/points.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["items"]:
            properties = {
                "ref": location["n"],
                "lat": location["l"]["a"],
                "lon": location["l"]["o"],
                "housenumber": location["b"],
                "street": location["e"],
                "city": location["c"],
                "state": location["r"].title(),
                "postcode": location["o"],
                "image": "https://geowidget.easypack24.net/uploads/pl/images/" + location["n"] + ".jpg",
                "opening_hours": OpeningHours(),
            }
            if location["h"] == "24/7":
                properties["opening_hours"].add_days_range(DAYS, "00:00", "23:59")
            else:
                properties["opening_hours"].add_ranges_from_string(location["h"], days=DAYS_PL)
            slug_parts = []
            if location["t"] == 1:
                apply_category(Categories.PARCEL_LOCKER, properties)
                slug_parts = ["parcel-locker", location["g"], location["n"], location["e"], "paczkomaty", location["r"]]
            elif location["t"] == 2:
                apply_category(Categories.PRODUCT_PICKUP, properties)
                slug_parts = ["parcel-service-point", location["n"], location["g"], location["e"]]
            if len(slug_parts) > 0:
                slug = "-".join(map(lambda x: unidecode(x.strip().lower()), slug_parts))
                properties["website"] = "https://inpost.pl/en/" + slug
            yield Feature(**properties)
