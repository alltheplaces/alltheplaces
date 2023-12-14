import urllib.parse

import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class MuellerSpider(scrapy.Spider):
    name = "mueller"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    storefinders = {
        "www.mueller.at": "/meine-filiale",
        "www.mueller.ch": "/meine-filiale",
        "www.mueller.de": "/meine-filiale",
        "www.mueller.es": "/mis-tiendas",
        "www.mueller.hr": "/moja-poslovnica",
        "www.mueller.co.hu": "/mueller-uezletek",
        "www.mueller.si": "/poslovalnice",
    }
    allowed_domains = storefinders.keys()
    start_urls = ["https://%s/api/ccstore/allPickupStores/" % d for d in storefinders]
    download_delay = 0.2

    def parse(self, response):
        store_numbers = [s["storeNumber"] for s in response.json()]
        for n in store_numbers:
            url = response.urljoin(f"/api/ccstore/byStoreNumber/{n}/")
            yield scrapy.Request(url, callback=self.parse_stores)

    def parse_stores(self, response):
        store = response.json()
        details = store.get("cCStoreDtoDetails", {})
        properties = {
            "brand": "Müller",
            "brand_wikidata": "Q1958759",
            "lat": store["latitude"],
            "lon": store["longitude"],
            "branch": store["storeName"],
            "name": "Müller",
            "street_address": store["street"],
            "city": store["city"],
            "postcode": store["zip"],
            "country": store["country"],
            "opening_hours": self.parse_opening_hours(store),
            "phone": details.get("phone", "").replace("/", " "),
            "website": self.parse_website(response, store),
            "ref": store["storeNumber"],
        }
        feature = Feature(**properties)
        apply_category(Categories.SHOP_CHEMIST, feature)
        yield feature

    def parse_opening_hours(self, store):
        store_hours = store.get("ccStoreDetails", {}).get("openingHourWeek")
        if not store_hours:
            return None
        opening_hours = OpeningHours()
        for record in store_hours:
            if record["open"]:
                opening_hours.add_range(
                    day=DAYS_EN[record["dayOfWeek"].title()],
                    open_time=record["fromTime"],
                    close_time=record["toTime"],
                    time_format="%H:%M",
                )
        return opening_hours.as_opening_hours()

    def parse_website(self, response, store):
        domain = urllib.parse.urlsplit(response.url).netloc
        finder = self.storefinders[domain]
        return response.urljoin("%s/%s" % (finder, store["link"]))
