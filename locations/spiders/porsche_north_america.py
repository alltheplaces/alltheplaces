import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours


class PorscheNorthAmericaSpider(scrapy.Spider):
    name = "porsche_north_america"
    item_attributes = {"brand": "Porsche", "brand_wikidata": "Q40993"}
    countries = ["us", "ca"]

    def start_requests(self):
        for country in self.countries:
            for city in city_locations(country, 50000):
                url = f"https://configurator.porsche.com/api/dealer-search/{country.upper()}/dealers?coordinates={city['latitude']}%2C{city['longitude']}"
                yield scrapy.Request(url, callback=self.parse, cb_kwargs={"country": country})

    def parse(self, response, country):
        for dealer in response.json():
            shop_info = dealer.get("dealer", {})
            item = DictParser.parse(shop_info)
            item["country"] = country
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("street")
            item["phone"] = shop_info.get("contactDetails", {}).get("phoneNumber")
            item["email"] = shop_info.get("contactDetails", {}).get("emailAddress")
            item["website"] = shop_info.get("contactDetails", {}).get("homepage")
            self.parse_hours(shop_info.get("contactDetails", {}).get("contactOpeningHours"), item)

            apply_category(Categories.SHOP_CAR, item)

            yield item

    def parse_hours(self, hours, item):
        if hours:
            oh = OpeningHours()
            for day in hours:
                oh.add_range(day["day"], day["open"], day["close"])

            item["opening_hours"] = oh
