from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class SaksFifthAvenueUSSpider(Spider):
    name = "saks_fifth_avenue_us"
    item_attributes = {"brand": "Saks Fifth Avenue", "brand_wikidata": "Q2723882"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://saksfifthavenue.brickworksoftware.com/locations/en/api/v2/stores"]

    def parse(self, response):
        for location in response.json()["stores"]:
            item = Feature(
                ref=location["id"],
                branch=location["name"],
                street_address=location["address_1"],
                city=location["city"],
                state=location["state"],
                postcode=location["postal_code"],
                country=location["country_code"],
                lat=location["latitude"],
                lon=location["longitude"],
                phone=location["phone_number"],
                email=location["email"],
                website=response.urljoin(location["url"]),
            )

            if address_2 := location["address_2"]:
                if address_2.lower().startswith("floor"):
                    item["unit"] = address_2
                else:
                    item["located_in"] = address_2

            hours = OpeningHours()
            for day_number, day in enumerate(DAYS_FROM_SUNDAY):
                if not (rules := location["regular_hours"].get(str(day_number))):
                    hours.set_closed(day)
                    continue
                for rule in rules:
                    hours.add_range(day, rule["open_at"], rule["close_at"])
            item["opening_hours"] = hours

            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            yield item
