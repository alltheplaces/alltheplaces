from locations.categories import Categories, apply_category
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.algolia import AlgoliaSpider


class BaptistHealthArkansasUSSpider(AlgoliaSpider):
    name = "baptist_health_arkansas_us"
    item_attributes = {
        "brand": "Baptist Health Foundation",
        "brand_wikidata": "Q50379824",
    }
    api_key = "66eafc59867885378e0a81317ea35987"
    app_id = "6EH1IB012D"
    index_name = "wp_posts_location"

    def parse_item(self, item, location):
        item["name"] = location["post_title"]
        item["ref"] = location["permalink"]
        item["website"] = location["permalink"]
        item["image"] = location["image"]
        item["street_address"] = merge_address_lines([location["address_1"], location["address_2"]])
        item["city"] = location["city"]
        item["state"] = location["state"]
        item["postcode"] = location["zip_code"]
        item["country"] = "US"
        item["phone"] = location["phone_number"]
        item["lat"] = float(location["_geoloc"]["lat"])
        item["lon"] = -abs(float(location["_geoloc"]["lng"]))
        if facility_type := location.get("facility_type"):
            if "Hospitals" in facility_type:
                apply_category(Categories.HOSPITAL, item)
            elif "Urgent Care" in facility_type:
                apply_category(Categories.CLINIC_URGENT, item)
            else:
                apply_category(Categories.CLINIC, item)
        yield item
