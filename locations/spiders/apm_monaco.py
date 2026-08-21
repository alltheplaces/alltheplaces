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

        fields = [
            location.get("custom_field_1") or "",
            location.get("custom_field_2") or "",
            location.get("custom_field_3") or "",
        ]

        if any(fields):
            oh = OpeningHours()
            oh.add_ranges_from_string(" ".join(fields))
            item["opening_hours"] = oh
        else:
            item["opening_hours"] = None

        yield item
