import scrapy

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature


class VodafoneziggoNLSpider(scrapy.Spider):
    name = "vodafoneziggo_nl"
    item_attributes = {"brand": "VodafoneZiggo", "brand_wikidata": "Q55640416"}
    start_urls = [
        "https://api.localistico.com/clients/v1/businesses/694cbc6c-9274-48b0-b509-f989f7febed2/locations/45bca548-ee7a-4640-94dc-22d919f3f5ce.json?access_token=U0UsaiI5Tv4bHvizsfJGXdqlL6Il11lCMFjJaUmc8_exoYaIx7zzNbRdygnTIg7viBQ"
    ]

    def parse(self, response):
        for location in response.json():
            if location.get("close") != "no":
                continue

            item = Feature()
            item["ref"] = location["location_code"]
            item["name"] = location["location_name"]
            item["street_address"] = location["street_address"]
            item["postcode"] = location["postcode"]
            item["city"] = location["locality"]
            item["state"] = location["region"]
            item["country"] = location["country_code"]
            item["lat"] = location["location_lat"]
            item["lon"] = location["location_lng"]

            item["opening_hours"] = OpeningHours()
            for day_hours in location.get("hours", "").split("|"):
                day, _, times = day_hours.partition(":")
                if not times:
                    continue
                for interval in times.split(","):
                    open_time, _, close_time = interval.partition("-")
                    if open_time and close_time:
                        item["opening_hours"].add_range(DAYS_EN.get(day, day), open_time, close_time)

            apply_category(Categories.SHOP_MOBILE_PHONE, item)

            yield item
