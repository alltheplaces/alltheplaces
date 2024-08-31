from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider


class IowaUniversityUSSpider(AlgoliaSpider):
    name = "iowa_university_us"
    item_attributes = {
        "brand": "University of Iowa Hospitals and Clinics",
        "brand_wikidata": "Q7895561",
    }
    app_id = "6X6RKBA85V"
    api_key = "82d9c12b5c362e709520d802b71137ce"
    index_name = "uihc_locations"
    referer = "https://uihc.org/locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["objectID"]
        item["street_address"] = feature["field_address:thoroughfare"]
        item["city"] = feature["field_address:locality"]
        item["state"] = feature["field_address:administrative_area"]
        item["postcode"] = feature["field_address:postal_code"]
        item["lat"] = feature["field_geolocation:lat"]
        item["lon"] = feature["field_geolocation:lon"]
        item["phone"] = feature.get("field_location_phone")
        if services := feature.get("services"):
            if "Same-Day Care" in services:
                apply_category(Categories.CLINIC, item)
            else:
                apply_category(Categories.HOSPITAL, item)
        else:
            apply_category(Categories.CLINIC, item)
        yield item
