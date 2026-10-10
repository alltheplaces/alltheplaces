from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class RustyBucketUSSpider(Spider):
    name = "rusty_bucket_us"
    item_attributes = {"brand": "Rusty Bucket Restaurant & Tavern", "brand_wikidata": "Q7382574"}
    start_urls = ["https://myrustybucket.com/wp-json/wp/v2/locations?per_page=100&_fields=id,link,title,location_info"]

    def parse(self, response):
        for location in response.json():
            details = location["location_info"]
            address = details["address"]
            item = Feature(
                ref=location["id"],
                branch=location["title"]["rendered"],
                street_address=f'{address["street_number"]} {address["street_name"]}',
                city=address["city"],
                state=address["state_short"],
                postcode=address["post_code"],
                country=address["country_short"],
                lat=address["lat"],
                lon=address["lng"],
                phone=details["phone_number"],
                website=location["link"],
            )

            hours = OpeningHours()
            for day, rule in details["hours"]["days"].items():
                day = DAYS_EN[day.title()]
                if rule["closed"]:
                    hours.set_closed(day)
                else:
                    hours.add_range(day, rule["open"], rule["close"], time_format="%I:%M %p")
            item["opening_hours"] = hours

            apply_category(Categories.RESTAURANT, item)
            yield item
