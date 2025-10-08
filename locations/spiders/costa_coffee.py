from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.country_utils import CountryUtils
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class CostaCoffeeSpider(Spider):
    name = "costa_coffee"
    COSTA = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    COSTA_EXPRESS = {"brand": "Costa Express", "brand_wikidata": "Q113556385"}
    SMART_CAFE = {"brand": "Smart Café", "brand_wikidata": "Q117448428"}
    start_urls = [
        # "https://bg.costacoffee.com/",
        "https://www.costa-coffee.be/api/cf/?content_type=storeLocatorStore",
        # "https://www.costa-coffee.rs/",
        # Cyprus
        # "https://cz.costacoffee.com/",
        "https://www.costacoffee.de/api/cf/?content_type=storeLocatorStore",
        "https://www.costacoffee.eg/api/cf/?content_type=storeLocatorStore",
        "https://www.costacoffee.es/api/cf/?content_type=storeLocatorStore",
        # "https://www.costacoffee.gr/",
        # "https://www.costacoffee.hr/",
        "https://www.costacoffee.in/api/cf/?content_type=storeLocatorStore",
        "https://www.costaireland.ie/api/cf/?content_type=storeLocatorStore",
        "https://www.costacoffee.jp/api/cf/?content_type=storeLocatorStore",
        # "https://www.costakuwait.com/locations.json",
        # "https://www.costa.lv/lv/kafejnicas/",
        # Lëtzebuerg
        # "https://hu.costacoffee.com/",
        # "https://www.costacoffeemalaysia.com/",
        # "https://www.costamalta.com/en/locations",
        # "https://www.costacoffee.mx/en",
        # "https://www.costa-coffee.at/",
        # "https://www.costacoffee.pl/", # CostaCoffeePLSpider
        # "https://www.costacoffee.ro/",
        # "https://www.costaksa.com/locations.json",
        # "https://costacoffee.si/",
        # "https://sk.costacoffee.com/",
        # "https://www.costa-coffee.ch/en",
        "https://www.costacoffee.ae/api/cf/?content_type=storeLocatorStore",
        # "https://www.costa.co.uk/",  # CostaCoffeeGBSpider
        "https://us.costacoffee.com/api/cf/?content_type=storeLocatorStore",
    ]
    page_size = 1000

    # Unfortunately each country has their own "types"
    store_types = {
        "Airport": (COSTA, Categories.COFFEE_SHOP),
        "Briggo": None,  # Unknown, only 1
        "COFFEEMAKER": ({"brand": "Costa Coffee"}, Categories.VENDING_MACHINE),
        "COSTA EXPRESS": (COSTA_EXPRESS, Categories.VENDING_MACHINE),
        "COSTA PARTNER": None,  # Third party
        "COSTA STORE": (COSTA, Categories.COFFEE_SHOP),
        "City": (COSTA, Categories.COFFEE_SHOP),
        "Corporate": (COSTA, Categories.COFFEE_SHOP),
        "Costa Proud to Serve": None,  # Third party
        "Hospital": (COSTA, Categories.COFFEE_SHOP),
        "Mall": (COSTA, Categories.COFFEE_SHOP),
        "Marlow": (COSTA, Categories.COFFEE_SHOP),
        "Proud to Serve": None,  # Third party
        "Smart Café": (SMART_CAFE, Categories.VENDING_MACHINE),
        "Store": (COSTA, Categories.COFFEE_SHOP),
    }

    def __init__(self):
        self.country_utils = CountryUtils()

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=f"{url}&limit={self.page_size}")

    def parse(self, response):
        entries = {}
        for entry in response.json()["includes"]["Entry"]:
            entries[entry["sys"]["id"]] = entry["fields"]["name"]

        if "us.costacoffee.com" in response.url:
            country = "US"
        else:
            country = self.country_utils.country_code_from_url(response.url)

        for location in response.json()["items"]:
            item = DictParser.parse(location["fields"])

            item["ref"] = location["sys"]["id"]
            item["addr_full"] = location["fields"]["storeAddress"]
            item["country"] = country

            item["opening_hours"] = OpeningHours()
            for day_name in [s.lower() for s in DAYS_FULL]:
                open_time = location["fields"].get(f"{day_name}Opening")
                close_time = location["fields"].get(f"{day_name}Closing")
                if open_time and "24 HOURS" in open_time.upper():
                    item["opening_hours"].add_range(day_name, "00:00", "24:00")
                elif open_time and close_time:
                    item["opening_hours"].add_range(day_name, open_time, close_time)

            store_type = entries[location["fields"]["storeType"]["sys"]["id"]]

            if brand := self.store_types.get(store_type):
                item.update(brand[0])
                apply_category(brand[1], item)
                yield item  # Only return know types
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/{store_type}/")

        offset = response.json()["skip"]
        if offset + response.json()["limit"] < response.json()["total"]:
            yield JsonRequest(url=f"{response.request.url}&limit={self.page_size}&offset={offset}")
