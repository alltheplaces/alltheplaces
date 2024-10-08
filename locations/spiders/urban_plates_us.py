from scrapy import FormRequest, Spider

from locations.categories import Categories, Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class UrbanPlatesUSSpider(Spider):
    name = "urban_plates_us"
    item_attributes = {
        "brand": "Urban Plates",
        "brand_wikidata": "Q96413021",
        "name": "Urban Plates",
        "extras": Categories.FAST_FOOD.value,
    }

    def start_requests(self):
        yield FormRequest(
            "https://api.urbanplates.com/proxy.php", formdata={"route": "/stores?all_stores=true", "method": "GET"}
        )

    def parse(self, response):
        for location in response.json()["response"]:
            # Copied from website code: skip customer service store
            if location["store_id"] == "900":
                continue

            item = DictParser.parse(location)

            item["website"] = f"https://urbanplates.com/store-details/?store_id={location['store_id']}"
            item["image"] = f"https://urbanplates.com/assets/img/locations/{location['store_id']}.jpg"
            item["branch"] = item.pop("name")

            apply_yes_no(
                Extras.DELIVERY,
                item,
                any(service["group_name"] == "delivery" and service["is_visible"] for service in location["services"]),
            )
            apply_yes_no(
                Extras.TAKEAWAY,
                item,
                any(service["group_name"] == "pickup" and service["is_visible"] for service in location["services"]),
            )

            oh = OpeningHours()
            for day in location["hours"]:
                oh.add_range(DAYS[day["day_of_week"]], day["start_time"], day["end_time"])
            item["opening_hours"] = oh

            yield item
