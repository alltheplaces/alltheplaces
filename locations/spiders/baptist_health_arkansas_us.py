from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
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

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature["post_title"]
        item["ref"] = feature["permalink"]
        item["street_address"] = merge_address_lines([feature["address_1"], feature["address_2"]])
        item["lat"] = float(feature["_geoloc"]["lat"])
        item["lon"] = -abs(float(feature["_geoloc"]["lng"]))
        if facility_type := feature.get("facility_type"):
            if "Hospitals" in facility_type:
                apply_category(Categories.HOSPITAL, item)
            elif "Urgent Care" in facility_type:
                apply_category(Categories.CLINIC_URGENT, item)
            else:
                apply_category(Categories.CLINIC, item)
        yield item
