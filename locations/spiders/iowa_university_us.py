from locations.categories import Categories, apply_category
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

    def parse_item(self, item, location):
        item["ref"] = location["objectID"]
        item["street_address"] = location["address"]["thoroughfare"]
        item["city"] = location["address"]["locality"]
        item["state"] = location["address"]["administrative_area"]
        item["postcode"] = location["address"]["postal_code"]
        item["lat"] = location["geolocation"]["lat"]
        item["lon"] = location["geolocation"]["lon"]
        item["phone"] = location.get("location_phone")
        if services := location.get("services"):
            if "Same-Day Care" in services:
                apply_category(Categories.CLINIC, item)
            else:
                apply_category(Categories.HOSPITAL, item)
        else:
            apply_category(Categories.CLINIC, item)
        yield item
