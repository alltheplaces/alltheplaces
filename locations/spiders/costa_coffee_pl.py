import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class CostaCoffeePLSpider(scrapy.Spider):
    name = "costa_coffee_pl"
    item_attributes = {"brand": "Costa Coffee", "brand_wikidata": "Q608845"}
    allowed_domains = ["costacoffee.pl"]
    start_urls = ["https://www.costacoffee.pl/api/cf/?content_type=storeLocatorStore&limit=1000"]
    no_refs = True
    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt is a HTML 404 page, ignore to suppress errors

    def parse(self, response):
        data = response.json()["items"]
        for store in data:
            properties = {
                "name": store["fields"]["cmsLabel"],
                "addr_full": store["fields"]["storeAddress"],
                "country": "PL",
                "lat": store["fields"]["location"]["lat"],
                "lon": store["fields"]["location"]["lon"],
                "opening_hours": OpeningHours(),
            }

            for day_name in list(map(str.lower, DAYS_FULL)):
                opening_time = store["fields"].get(f"{day_name}Opening")
                closing_time = store["fields"].get(f"{day_name}Closing")
                if not opening_time or not closing_time:
                    continue
                properties["opening_hours"].add_range(day_name.title(), opening_time, closing_time)

            apply_category(Categories.CAFE, properties)

            yield Feature(**properties)
