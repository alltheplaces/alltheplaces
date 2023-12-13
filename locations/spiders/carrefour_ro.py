import chompjs
from scrapy import Selector, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_RO, OpeningHours
from locations.spiders.carrefour_fr import (
    CARREFOUR_CONTACT,
    CARREFOUR_EXPRESS,
    CARREFOUR_MARKET,
    CARREFOUR_SUPERMARKET,
    parse_brand_and_category_from_mapping,
)


class CarrefourROSpider(Spider):
    name = "carrefour_ro"
    allowed_domains = ["carrefour.ro"]
    start_urls = ["https://carrefour.ro/corporate/magazine"]

    brands = {
        "Contact": CARREFOUR_CONTACT,
        "Express": CARREFOUR_EXPRESS,
        "Express portocaliu": CARREFOUR_EXPRESS,  # Express - "Orange" store (?)
        "Express Franciza": CARREFOUR_EXPRESS,  # Express - Franchise store
        "Hipermarket": CARREFOUR_SUPERMARKET,
        "Market": CARREFOUR_MARKET,
    }

    def parse(self, response):
        js_dict = (
            response.xpath('//script[contains(text(), "app.stores = app.allStores = ")]/text()')
            .get()
            .split("app.stores = app.allStores = ", 1)[1]
            .split("}];", 1)[0]
            + "}]"
        )
        for location in chompjs.parse_js_object(js_dict):
            item = DictParser.parse(location)
            if not location["status"]:
                continue
            if (
                not location.get("type")
                or not location["type"].get("name")
                or location["type"]["name"] not in self.brands.keys()
            ):
                # Location is a warehouse or headquarters. Ignore it.
                continue

            parse_brand_and_category_from_mapping(item, location["type"]["name"], self.brands)

            item["street_address"] = item.pop("addr_full")
            item["city"] = location["city"]["name"]
            item["website"] = (
                "https://carrefour.ro/corporate/magazine/" + location["city"]["slug"] + "/" + location["slug"]
            )
            schedule_html = Selector(text=location["schedule"])
            hours_string = " ".join(filter(None, schedule_html.xpath("//text()").getall()))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_RO, named_day_ranges={})
            yield item
