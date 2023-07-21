from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature, add_social_media
from locations.spiders.vapestore_gb import clean_address


class TigerWheelAndTyreZASpider(Spider):
    name = "tiger_wheel_and_tyre_za"
    item_attributes = {"brand": "Tiger Wheel & Tyre", "brand_wikidata": "Q120762656"}
    start_urls = [
        "https://api.locationbank.net/storelocator/StoreLocatorAPI?clientId=229c9ffb-f729-4455-b0a2-ac61974c7074"
    ]

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            item = Feature()
            item["ref"] = location["storeCode"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["name"] = location["locationName"]
            item["street_address"] = clean_address(
                [
                    location["addressLine1"],
                    location["addressLine2"],
                    location["addressLine3"],
                    location["addressLine4"],
                    location["addressLine5"],
                ]
            )
            item["extras"]["addr:town"] = location["subLocality"]
            item["city"] = location["locality"]
            item["state"] = location["administrativeArea"]
            item["country"] = location["country"]
            item["postcode"] = location["postalCode"]
            item["website"] = f'https://www.twt.co.za/store-details/?locationid={location["id"]}'
            item["phone"] = location["primaryPhone"]
            item["email"] = location["email"]

            item["opening_hours"] = OpeningHours()
            for rule in location["regularHours"]:
                if not rule["isOpen"]:
                    continue
                item["opening_hours"].add_range(rule["openDay"], rule["openTime"], rule["closeTime"])

            for social_media in location["socialMedia"]:
                add_social_media(item, social_media["name"], social_media["url"])

            yield item
