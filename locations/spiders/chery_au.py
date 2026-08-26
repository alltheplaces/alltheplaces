from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class CheryAUSpider(JSONBlobSpider):
    name = "chery_au"
    item_attributes = {"brand": "Chery", "brand_wikidata": "Q591001"}
    start_urls = ["https://cherymotor.com.au/api/dealers/0/0/empty"]

    def pre_process_data(self, feature: dict) -> None:
        feature["ref"] = feature["code"]

    def post_process_item(self, item, response, feature):
        apply_category(Categories.SHOP_CAR, item)

        item["state"] = feature.get("address", {}).get("administrative_area")

        # Prefer the dealer's own website over the relative link to its profile
        # page on cherymotor.com.au, which DictParser would otherwise pick up
        # via the "url" field.
        item["website"] = feature.get("website") or response.urljoin(feature.get("url", ""))

        if phone := feature.get("phone"):
            # A small number of source records contain stray Unicode formatting
            # characters (e.g. U+202D) mixed into the phone number.
            item["phone"] = "".join(ch for ch in phone if ch.isprintable())

        oh = OpeningHours()
        for hours in feature.get("open_hours", []):
            if content := hours.get("content"):
                oh.add_ranges_from_string(content)
        item["opening_hours"] = oh

        yield item
