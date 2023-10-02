import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.spiders.carrefour_fr import (
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)


class CarrefourARSpider(scrapy.Spider):
    name = "carrefour_ar"
    # TODO: I suspect other Carrefour domains have this very same interface
    # TODO: Figure out how to handle change of sha256Hash of persistedQuery.
    start_urls = [
        """https://www.carrefour.com.ar/_v/public/graphql/v1?workspace=master&maxAge=short&appsEtag=remove&domain=store&locale=es-AR&operationName=getStoreLocations&extensions={"persistedQuery":{"version":1,"sha256Hash":"81646d6f8cea93c5500fb78cce9a7e282b0a8585bb77079f6085d8e7f5036127","sender":"valtech.carrefourar-store-locator@0.x","provider":"vtex.store-graphql@2.x"},"variables":"eyJhY2NvdW50IjoiY2FycmVmb3VyYXIifQ=="}"""
    ]

    brands = {
        "Express": CARREFOUR_EXPRESS,
        "Hipermercado": CARREFOUR_SUPERMARKET,
        "Market": CARREFOUR_MARKET,
        "Maxi": CARREFOUR_SUPERMARKET,
    }

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

            if not parse_brand_and_category_from_mapping(item, o.get("labels"), self.brands):
                self.crawler.stats.inc_value(f'atp/carrefour_ar/unknown_brand/{o.get("labels")}')

            oh = OpeningHours()
            for day in DAYS_FULL:
                if rule := o.get(day.lower() + "Hours"):
                    if rule == "Cerrado" or "-" not in rule or "/" in rule or "," in rule:  # Closed
                        continue
                    open_time, close_time = rule.split("-")
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh.as_opening_hours()

            yield item
