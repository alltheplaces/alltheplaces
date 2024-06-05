import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BQSpider(scrapy.Spider):
    name = "bq"
    item_attributes = {"brand": "B&Q", "brand_wikidata": "Q707602"}
    allowed_domains = ["www.diy.com"]
    # To get a new atmosphere_app_id key, check Network calls within https://www.diy.com/find-a-store/ (call to api.kingfisher.com)
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {"Authorization": "Atmosphere atmosphere_app_id=kingfisher-7c4QgmLEROp4PUh0oUebbI94"}
    }

    start_urls = ("https://api.kingfisher.com/v1/mobile/stores/BQUK?nearLatLong=51.515617%2C-0.091998&page[size]=500",)

    def parse(self, response):
        for data in response.json()["data"]:
            store = data["attributes"]["store"]

            store["contact"] = store.pop("contactPoint")
            store["location"] = store["geoCoordinates"].pop("coordinates")

            item = DictParser.parse(store)

            item["ref"] = data["id"]
            item["website"] = "https://www.diy.com/store/" + item["ref"]

            item["country"] = store["geoCoordinates"]["countryCode"]
            item["postcode"] = store["geoCoordinates"]["postalCode"]

            item["addr_full"] = clean_address(store["geoCoordinates"]["address"]["lines"])
            item["street_address"] = clean_address(store["geoCoordinates"]["address"]["lines"][:3])
            oh = OpeningHours()
            for rule in store["openingHoursSpecifications"]:
                if not rule.get("opens"):
                    continue
                oh.add_range(rule["dayOfWeek"], rule["opens"][:5], rule["closes"][:5])
            item["opening_hours"] = oh.as_opening_hours()

            yield item
