from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES


class ToyotaCASpider(JSONBlobSpider):
    name = "toyota_ca"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = ["https://www.toyota.ca/toyota/data/dealer/.json"]
    locations_key = "dealers"

    def pre_process_data(self, location):
        location["name_dict"] = location.pop("name")
        location["name"] = location["name_dict"].get("en")

    def post_process_item(self, item, response, location):
        departments = [d["name"]["en"] for d in location["departments"]]
        if "New Vehicle Sales" in departments:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.USED_CAR_SALES, item, "Pre-owned Vehicle Sales" in departments)
            apply_yes_no(Extras.CAR_PARTS, item, "Parts" in departments)
            apply_yes_no(Extras.CAR_REPAIR, item, "Service" in departments)
        elif "Pre-owned Vehicle Sales" in departments:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_PARTS, item, "Parts" in departments)
            apply_yes_no(Extras.CAR_REPAIR, item, "Service" in departments)
        elif "Service" in departments:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            apply_yes_no(Extras.CAR_PARTS, item, "Parts" in departments)
        elif "Parts" in departments:
            apply_category(Categories.SHOP_CAR_PARTS, item)

        if location["name_dict"].get("en") != location["name_dict"].get("fr"):
            item["extras"]["name:en"] = location["name_dict"].get("en")
            item["extras"]["name:fr"] = location["name_dict"].get("fr")
        item["phone"] = "; ".join([phone["CompleteNumber"]["$"] for phone in location["phoneNumbers"]])

        item["opening_hours"] = OpeningHours()
        for department in location["departments"]:
            if department["name"]["en"] == "New Vehicle Sales":
                for hour in department["hours"]:
                    if "toDay" in hour:
                        item["opening_hours"].add_ranges_from_string(
                            f"{hour['fromDay']['en']}-{hour['toDay']['en']} {hour['startTime']['en']}-{hour['endTime']['en']}"
                        )
                    else:
                        item["opening_hours"].add_ranges_from_string(
                            f"{hour['fromDay']['en']} {hour['startTime']['en']}-{hour['endTime']['en']}"
                        )
            elif "hours" in department:
                self.crawler.stats.inc_value(f"atp/{self.name}/other_opening_hours_type/{department['name']['en']}")

        yield item
