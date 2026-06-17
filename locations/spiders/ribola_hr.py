import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_HR, OpeningHours
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class RibolaHRSpider(WpGoMapsSpider):
    name = "ribola_hr"
    item_attributes = {
        "brand": "Ribola",
        "brand_wikidata": "Q65124070",
    }
    allowed_domains = ["ribola.hr"]
    map_id = 4
    requires_proxy = "HR"

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        if name := item.pop("name"):
            if m := re.match(r"Ribola (\d+) ", name):
                item["ref"] = m.group(1)
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(location["description"], days=DAYS_HR)
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
