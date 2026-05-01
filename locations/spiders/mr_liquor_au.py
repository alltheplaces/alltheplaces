from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class MrLiquorAUSpider(JSONBlobSpider):
    name = "mr_liquor_au"
    item_attributes = {"brand": "Mr Liquor", "brand_wikidata": "Q117822077"}
    start_urls = ["https://storelocator.metizapps.com/v2/api/front/store-locator/?shop=mr-liquor.myshopify.com"]
    locations_key = "stores"

    def post_process_item(self, item, response, location):
        if not location.get("storename"):
            return

        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        # to avoid clean_strings warning for addr_full
        item["addr_full"] = location.get("address").strip()
        location["lat"] = location.get("mapLatitude")
        location["lon"] = location.get("mapLongitude")

        if "SOON" not in (hours_raw := location.get("hour_of_operation")):
            oh = OpeningHours()
            oh.add_ranges_from_string(hours_raw)
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_ALCOHOL, item)

        yield item
