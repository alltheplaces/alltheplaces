import json
from typing import Iterable

from scrapy.http import FormRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class PointSFRSpider(JSONBlobSpider):
    name = "point_s_fr"
    item_attributes = {"brand": "Point S", "brand_wikidata": "Q3393358"}
    locations_key = ["data", "centers"]

    async def start(self):
        yield FormRequest(
            url="https://www.points.fr/wp-admin/admin-ajax.php", formdata={"action": "center_list", "filters": ""}
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        item["country"] = "FR"
        item["branch"] = item.pop("name", "")

        schedule = feature.pop("schedules")
        if schedule:
            try:
                item["opening_hours"] = OpeningHours()
                data = json.loads(schedule)
                for i in data:
                    day = data[i]
                    item["opening_hours"].add_ranges_from_string(
                        day["day"] + " " + day["label"].replace("h", ":").replace("et de", ""),
                        DAYS_FR,
                        delimiters=DELIMITERS_FR,
                        closed=CLOSED_FR,
                    )
            except json.JSONDecodeError:
                pass

        yield item
