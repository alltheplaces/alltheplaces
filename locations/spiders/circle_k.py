import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class CircleKSpider(Spider):
    name = "circle_k"
    CIRCLE_K = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    allowed_domains = ["www.circlek.com"]
    start_urls = ["https://www.circlek.com/stores_master.php?lat=0&lng=0&page=0"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    brands = {
        "Car Wash Cleanfreak": ({"name": "Clean Freak Car Wash", "brand": "Clean Freak Car Wash"}, Categories.CAR_WASH),
        "Circle K": (CIRCLE_K, None),
        "Corner Store": ({"name": "Corner Store", "brand": "Corner Store"}, Categories.SHOP_CONVENIENCE),
        "Couche-Tard": ({"brand": "Couche-Tard", "brand_wikidata": "Q2836957"}, None),
        "Holiday Station": ({"brand": "Holiday", "brand_wikidata": "Q5880490"}, None),
        "Kangaroo Express": ({"brand": "Kangaroo Express", "brand_wikidata": "Q61747408"}, Categories.SHOP_CONVENIENCE),
        "Mac's": ({"name": "Mac's", "brand": "Mac's", "brand_wikidata": "Q4043527"}, Categories.SHOP_CONVENIENCE),
        "On the Run": ({"brand": "On the Run", "brand_wikidata": "Q16931259"}, Categories.SHOP_CONVENIENCE),
        "Rainstorm Car Wash": ({"name": "Rainstorm Car Wash", "brand": "Rainstorm Car Wash"}, Categories.CAR_WASH),
    }

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, meta={"page": 0})

    def parse(self, response):
        if response.json()["count"] == 0:
            # crawl completed
            return

        for location_id, location in response.json()["stores"].items():
            item = DictParser.parse(location)
            item["ref"] = location_id
            item["street_address"] = item.pop("addr_full")
            item["website"] = response.urljoin(location["url"])

            services = [service["name"] for service in location["services"]]
            apply_yes_no(Extras.ATM, item, "atm" in services)
            apply_yes_no(Extras.TOILETS, item, "public_restrooms" in services)
            apply_yes_no(Extras.CAR_WASH, item, "car_wash" in services)
            apply_yes_no(Fuel.DIESEL, item, "diesel" in services)
            apply_yes_no(Fuel.ELECTRIC, item, "ev_charger" in services)

            brand, cat = self.brands.get(location["display_brand"], (None, None))
            if brand:
                item.update(brand)
            else:
                self.crawler.stats.inc_value("x/{}".format(location["franchise_brand"]))
            if cat:
                apply_category(cat, item)
            else:
                if "gas" in services or "diesel" in services:
                    apply_category(Categories.FUEL_STATION, item)
                else:
                    apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item

        if response.json()["count"] < 10:
            # crawl completed
            return

        next_page = response.meta["page"] + 1
        next_url = re.sub(r"\d+$", str(next_page), response.url)
        yield JsonRequest(url=next_url, meta={"page": next_page})
