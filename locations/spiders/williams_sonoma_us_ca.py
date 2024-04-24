from json import loads

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class WilliamsSonomaUSCASpider(Spider):
    name = "williams_sonoma_us_ca"
    allowed_domains = ["www.williams-sonoma.com"]
    start_urls = [
        "https://www.williams-sonoma.com/search/stores.json?brands=WS,PB&lat=40.71304703&lng=-74.00723267&radius=100000&includeOutlets=false",
        "https://www.williams-sonoma.ca/search/stores.json?brands=WS,PB&lat=40.71304703&lng=-74.00723267&radius=100000&includeOutlets=false",
    ]
    brands = {
        "WS": {"brand": "Williams-Sonoma", "brand_wikidata": "Q2581220"},
        "PB": {"brand": "Pottery Barn", "brand_wikidata": "Q3400126"},
    }
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        # A quirk of scrapy-playwright is that the raw JSON response can't be
        # obtained as Playwright's Response object is not exposed. Instead, a
        # HTML wrapper is put around the raw JSON response, and thus we need
        # to extract from this HTML wrapper.
        json_blob = loads(response.xpath("//pre/text()").get())
        for location in json_blob["storeListResponse"]["stores"]:
            location = location["properties"]
            item = DictParser.parse(location)
            item.update(self.brands[location["BRAND"]])
            item["street_address"] = location["ADDRESS_LINE_1"]
            item["phone"] = location["PHONE_NUMBER_FORMATTED"]
            slug = "{}-{}-{}-{}".format(
                location["COUNTRY_CODE"].lower(),
                location["STATE_PROVINCE"].lower(),
                location["CITY"].lower().replace(" ", "-"),
                location["STORE_NAME"].lower().replace(" ", "-"),
            )
            if location["BRAND"] == "WS":
                apply_category(Categories.SHOP_HOUSEWARE, item)
                item["website"] = f"https://www.williams-sonoma.com/stores/{slug}/"
            elif location["BRAND"] == "PB":
                apply_category(Categories.SHOP_FURNITURE, item)
                item["website"] = f"https://www.potterybarn.com/stores/{slug}/"
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                day_hours = location.get("{}_HOURS_FORMATTED".format(day_name.upper()))
                if not day_hours:
                    continue
                item["opening_hours"].add_range(day_name, *day_hours.split(" - ", 1), "%I:%M %p")
            yield item
