import chompjs
from scrapy import Selector, Spider
from locations.categories import Categories

from locations.dict_parser import DictParser
from locations.hours import DAYS_RO, OpeningHours


class CarrefourROSpider(Spider):
    name = "carrefour_ro"
    allowed_domains = ["carrefour.ro"]
    start_urls = ["https://carrefour.ro/corporate/magazine"]

    brands = {
        "Hipermarket": {"brand": "Carrefour", "brand_wikidata": "Q217599", "extras": Categories.SHOP_SUPERMARKET.value},
        "Market": {
            "brand": "Carrefour Market",
            "brand_wikidata": "Q2689639",
            "extras": Categories.SHOP_SUPERMARKET.value,
        },
        "Express": {
            "brand": "Carrefour Express",
            "brand_wikidata": "Q2940190",
            "extras": Categories.SHOP_CONVENIENCE.value,
        },
        "Express portocaliu": {
            "brand": "Carrefour Express",
            "brand_wikidata": "Q2940190",
            "extras": Categories.SHOP_CONVENIENCE.value,
        },  # Express - "Orange" store (?)
        "Express Franciza": {
            "brand": "Carrefour Express",
            "brand_wikidata": "Q2940190",
            "extras": Categories.SHOP_CONVENIENCE.value,
        },  # Express - Franchise store
        "Contact": {
            "brand": "Carrefour Contact",
            "brand_wikidata": "Q2940188",
            "extras": Categories.SHOP_SUPERMARKET.value,
        },
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
            item.update(self.brands[location["type"]["name"]])
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
