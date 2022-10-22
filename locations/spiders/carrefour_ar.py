import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class CarrefourARSpider(scrapy.Spider):
    name = "carrefour_ar"
    item_attributes = {"brand": "Carrefour", "brand_wikidata": "Q217599"}
    # TODO: I suspect other Carrefour domains have this very same interface
    # TODO: Figure out why the hash changed. Will this happen again?
    start_urls = [
        "https://www.carrefour.com.ar/_v/public/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-AR&operationName=getStoreLocations&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22162654afe95c8f4ceabfa711ef355ce78a8988bd98ac5affe367f372703e15d6%22%2C%22sender%22%3A%22lyracons.lyr-store-locator%400.x%22%2C%22provider%22%3A%22vtex.store-graphql%402.x%22%7D%2C%22variables%22%3A%22eyJhY2NvdW50IjoiY2FycmVmb3VyYXIifQ%3D%3D%22%7D"
    ]

    def parse(self, response):
        for data in response.json()["data"]["documents"]:
            o = {}
            for field in data["fields"]:
                value = field.get("value", "null")
                if not value == "null":
                    o[field["key"]] = value
            o["name"] = o.get("businessName")
            o["phone"] = o.get("primaryPhone")
            o["city"] = o.get("locality")
            o["state"] = o.get("administrativeArea")
            item = DictParser.parse(o)

            oh = OpeningHours()
            for day in DAYS_FULL:
                if rule := o.get(day.lower() + "Hours"):
                    if (
                        rule == "Cerrado"  # Closed
                        or not "-" in rule
                        or "/" in rule
                        or "," in rule
                    ):
                        continue
                    open_time, close_time = rule.split("-")
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh.as_opening_hours()

            yield item
