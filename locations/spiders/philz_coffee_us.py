import json

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class PhilzCoffeeUSSpider(JSONBlobSpider):
    name = "philz_coffee_us"
    item_attributes = {"brand": "Philz Coffee", "brand_wikidata": "Q18156812"}
    start_urls = ["https://philzcoffee.com/locations"]

    def extract_json(self, response):
        return json.loads(response.xpath("//@data-locations-locations-value").get())

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name").strip()
        item["state"] = feature["state"]
        item["country"]="US"
        item["website"] = f"https://philzcoffee.com/locations/{item['ref']}"

        if feature["header_image_one_url"]:
            item["image"] = response.urljoin(feature["header_image_one_url"])

        oh = OpeningHours()
        for day in feature["hours"]:
            oh.add_range(day["day"], day["opens"], day["closes"])
        item["opening_hours"] = oh

        apply_yes_no(Extras.DRIVE_THROUGH, item, feature["has_drive_thru"])

        yield item
