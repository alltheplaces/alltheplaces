import json
from collections import Counter

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsGTSpider(JSONBlobSpider):
    name = "mcdonalds_gt"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.com.gt/restaurantes"]

    def extract_json(self, response):
        restaurants = json.loads(response.xpath("//@data-page").get())["props"]["restaurants"]
        self.shared_contacts = {
            key: {value for value, count in Counter(r.get(key) for r in restaurants).items() if count > 1}
            for key in ("phone", "email")
        }
        return restaurants

    def post_process_item(self, item, response, location):
        for key in ("phone", "email"):
            if location.get(key) in self.shared_contacts[key]:
                item[key] = None
        item["branch"] = item.pop("name")
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["categorias"])

        for oh_rules in (
            location["horarios"].values() if isinstance(location["horarios"], dict) else location["horarios"]
        ):
            if oh_rules["name"].startswith("Restaurante"):
                item["opening_hours"] = OpeningHours()
                for rule in oh_rules["horarios"]:
                    if day := sanitise_day(rule["description"], DAYS_ES):
                        item["opening_hours"].add_range(day, rule["start_time"], rule["end_time"])

        apply_category(Categories.FAST_FOOD, item)

        yield item
