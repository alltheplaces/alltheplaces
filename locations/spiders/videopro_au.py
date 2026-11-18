from locations.categories import Categories, apply_category
from locations.storefinders.localisr import LocalisrSpider


class VideoproAUSpider(LocalisrSpider):
    name = "videopro_au"
    item_attributes = {"brand": "Videopro", "brand_wikidata": "Q120648551"}
    api_key = "2RVE9OR1648JPW0X5EMRZNVQD3YK792GZO3PQ40"
    # The search radius appears to be ignored, so a single search
    # coordinate is returning locations all across Australia.
    search_coordinates = [
        (-27.4721959, 153.014815),
    ]

    def parse_item(self, item, location):
        if "WAREHOUSE" in item["name"].upper().split():
            return
        item["street_address"] = item.pop("addr_full", None)
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
