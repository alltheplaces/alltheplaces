from typing import Any, Counter

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaExpressGBSpider(Spider):
    name = "pizza_express_gb"
    item_attributes = {"brand": "PizzaExpress", "brand_wikidata": "Q662845"}
    start_urls = ["https://www.pizzaexpress.com/api/restaurants/FindRestaurantsByLatLong?limit=2000"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        restaurants = response.json()

        # Count how many times each image URL appears; drop any that are shared
        image_counts = Counter()
        for i in restaurants:
            if img := i.get("image"):
                if img.get("MediaExists") and img.get("Src"):
                    image_counts[img["Src"]] += 1

        for i in restaurants:
            item = DictParser.parse(i)
            item["branch"] = item.pop("name")

            item["ref"] = i["restaurantId"]
            item["addr_full"] = i["fullAddress"]
            item["postcode"] = i["Postcode"]
            item["website"] = response.urljoin(i["link"])
            item["street_address"] = merge_address_lines(
                [
                    i["Address1"],
                    i["Address2"],
                    i["Address3"],
                ],
            )

            if i["Location"] == "":
                item["city"] = i["fullAddress"].split(", ")[-2]
            else:
                item["city"] = i["Location"]

            if item["city"] == "Jersey":
                item["country"] = "JE"
                item["city"] = None
            else:
                item["country"] = "GB"

            if img := i.get("image"):
                if img.get("MediaExists") and img.get("Src") and image_counts[img["Src"]] == 1:
                    item["image"] = response.urljoin(img["Src"])

            facilities = [f["label"] for f in i["facilities"]]
            apply_yes_no(Extras.WHEELCHAIR, item, i["DisabledAccess"])
            apply_yes_no(Extras.TAKEAWAY, item, i["isOpenForCollection"], False)
            apply_yes_no(Extras.DELIVERY, item, i["isOpenForDelivery"], False)
            apply_yes_no(Extras.INDOOR_SEATING, item, i["isOpenForDineIn"], False)
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, "Disabled Toilet" in facilities)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, "Outdoor dining" in facilities)
            apply_yes_no(Extras.WIFI, item, "WiFi" in facilities)

            if i["openingHours"]:
                try:
                    item["opening_hours"] = self.parse_opening_hours(i["openingHours"])
                except Exception:
                    pass
            else:
                set_closed(item)
            if i["IsClosed"] or i["temporarilyClosed"]:
                set_closed(item)

            apply_category(Categories.RESTAURANT, item)

            yield item

    def parse_opening_hours(self, opening_hours: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            oh.add_range(rule["label"], *rule["value"].split("-"))
        return oh
