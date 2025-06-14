import re

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class BucaDiBeppoUSSpider(WpGoMapsSpider):
    name = "buca_di_beppo_us"
    item_attributes = {"brand": "Buca di Beppo", "brand_wikidata": "Q4982340"}
    allowed_domains = ["dineatbuca.com"]

    def post_process_item(self, item: Feature, location: dict) -> Feature:
        if m := re.search(r"Store #(\d+)$", location["title"]):
            item["ref"] = m.group(1)
        item.pop("name", None)
        if m := re.search(r"(\(\d{3}\) \d{3}-\d{4})", location["description"]):
            item["phone"] = m.group(1)
        apply_category(Categories.RESTAURANT, item)
        return item
