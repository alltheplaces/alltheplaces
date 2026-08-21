
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class ApmMonacoSpider(JSONBlobSpider):
    name = "apm_monaco"
    item_attributes = {
        "brand": "APM Monaco",
        "brand_wikidata": "Q85738954",
    }
    start_urls = ["https://storemapper-herokuapp-com.global.ssl.fastly.net/api/users/12892/stores.js"]
    locations_key = "stores"
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_JEWELRY, item)
        item["name"] = "APM Monaco"

        oh = OpeningHours()
        oh.add_ranges_from_string(
            location["custom_field_1"] + " " + location["custom_field_2"] + " " + location["custom_field_3"]
        )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
