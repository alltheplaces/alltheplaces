from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class OakFurniturelandGBSpider(JSONBlobSpider):
    name = "oak_furnitureland_gb"
    item_attributes = {"brand": "Oak Furnitureland", "brand_wikidata": "Q16959724"}
    start_urls = ["https://www.oakfurnitureland.co.uk/frontend_rest/frontend_showroom"]
    locations_key = "data"

    def pre_process_data(self, location: dict) -> None:
        location.pop("country", None)
        location["phone"] = location.pop("telephone_number", None)
        location["address"] = merge_address_lines([*location["address"].splitlines(), location["postal_code"]])

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs: Any) -> Iterable[Feature]:
        item["branch"] = item.pop("name").title()
        item["website"] = response.urljoin("/showrooms/" + location["showroom_landing_page"])

        item["opening_hours"] = OpeningHours()
        for day, rule in location["opening_hours"].items():
            if rule.get("closed"):
                item["opening_hours"].set_closed(day)
            elif rule.get("opens_at") and rule.get("closes_at"):
                item["opening_hours"].add_range(day, rule["opens_at"], rule["closes_at"])

        if location.get("is_closed") is True:
            set_closed(item)

        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
