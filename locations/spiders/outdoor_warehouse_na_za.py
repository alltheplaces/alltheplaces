import chompjs

from locations.hours import DAYS_FULL, OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class OutdoorWarehouseNAZASpider(JSONBlobSpider):
    name = "outdoor_warehouse_na_za"
    item_attributes = {
        "brand": "Outdoor Warehouse",
        "brand_wikidata": "Q130485369",
    }
    start_urls = ["https://www.outdoorwarehouse.co.za/store-locator"]
    skip_auto_cc_domain = True

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath("//store-selector").get())

    def post_process_item(self, item, response, location):
        item["branch"] = location.get("base_title")
        item.pop("name")

        if province := location.get("province"):
            item["state"] = province.get("title")
        elif region := location.get("geographic_region"):
            item["state"] = region.get("title")

        if isinstance(location.get("address_parts"), dict):
            item["addr_full"] = clean_address(list(location.get("address_parts").values()))
        elif isinstance(location.get("address_parts"), list):
            item["addr_full"] = clean_address(location.get("address_parts"))

        try:
            int(item["street_address"].split(" ")[0])
            item["housenumber"] = item["street_address"].split(" ")[0]
            item["street"] = item["street_address"].split(" ", 1)[1]
        except ValueError:
            pass

        item["website"] = f"https://www.outdoorwarehouse.co.za/store/{location['slug']}"

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            item["opening_hours"].add_range(
                day,
                location[f"{day.lower()}_open"].split("T")[1].split("+")[0],
                location[f"{day.lower()}_close"].split("T")[1].split("+")[0],
                time_format="%H:%M:%S",
            )

        yield item
