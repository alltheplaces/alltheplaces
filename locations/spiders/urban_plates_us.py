from scrapy import FormRequest

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class UrbanPlatesUSSpider(JSONBlobSpider):
    name = "urban_plates_us"
    item_attributes = {"brand": "Urban Plates", "brand_wikidata": "Q96413021"}
    locations_key = "response"

    async def start(self):
        yield FormRequest(
            "https://api.urbanplates.com/proxy-v2.php", formdata={"route": "/stores?all_stores=true", "method": "GET"}
        )

    def post_process_item(self, item, response, feature):
        # Copied from website code: skip customer service store
        if feature["store_id"] == "900":
            return

        item["website"] = f"https://urbanplates.com/store-details/?store_id={feature['store_id']}"
        item["image"] = f"https://urbanplates.com/assets/img/locations/{feature['store_id']}.jpg"
        item["branch"] = item.pop("name")

        apply_yes_no(
            Extras.DELIVERY,
            item,
            any(service["group_name"] == "delivery" and service["is_visible"] for service in feature["services"]),
        )
        apply_yes_no(
            Extras.TAKEAWAY,
            item,
            any(service["group_name"] == "pickup" and service["is_visible"] for service in feature["services"]),
        )

        oh = OpeningHours()
        for day in feature["hours"]:
            oh.add_range(DAYS[day["day_of_week"]], day["start_time"], day["end_time"])
        item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)

        yield item
