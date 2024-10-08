import json

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_ES, OpeningHours, sanitise_day
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsGTSpider(JSONBlobSpider):
    name = "mcdonalds_gt"
    item_attributes = McdonaldsSpider.item_attributes
    acustom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://mcdonalds.com.gt/restaurantes"]

    def extract_json(self, response):
        return json.loads(response.xpath("//@data-page").get())["props"]["restaurants"]

    def post_process_item(self, item, response, location):
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["categorias"])

        for oh_rules in (
            location["horarios"].values() if isinstance(location["horarios"], dict) else location["horarios"]
        ):
            if oh_rules["name"] == "Restaurante":
                item["opening_hours"] = OpeningHours()
                for rule in oh_rules["horarios"]:
                    if day := sanitise_day(rule["description"], DAYS_ES):
                        item["opening_hours"].add_range(day, rule["start_time"], rule["end_time"])

        yield item
