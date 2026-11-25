from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class ChipotleMiddleEastSpider(JSONBlobSpider):
    name = "chipotle_middle_east"
    item_attributes = { "brand": "Chipotle", "brand_wikidata": "Q465751" }
    start_urls = ["https://www.chipotleme.com/en/storefinderdata.json"]
    locations_key = "data"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    name_is_branch = True

    def post_process_item(self, item, response, feature):
        apply_category(Categories.FAST_FOOD, item)
        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            item["opening_hours"].add_range(day, *feature[f"{day.lower()}Hours"].replace(" ", "").split("-"))
        yield item
