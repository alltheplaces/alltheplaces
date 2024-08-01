from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.storefinders.algolia import AlgoliaSpider


class DunelmGBSpider(AlgoliaSpider):
    name = "dunelm_gb"
    item_attributes = {"name": "Dunelm", "brand": "Dunelm", "brand_wikidata": "Q5315020"}
    app_id = "FY8PLEBN34"
    api_key = "ae9bc9ca475f6c3d7579016da0305a33"
    index_name = "stores_prod"

    def parse_item(self, item, location):
        item["lat"] = location["_geoloc"]["lat"]
        item["lon"] = location["_geoloc"]["lng"]
        item["branch"] = item.pop("name")
        item["ref"] = location["sapStoreId"]
        item["website"] = "https://www.dunelm.com/stores/" + location["uri"]

        oh = OpeningHours()
        for rule in location["openingHours"]:
            oh.add_range(rule["day"], rule["open"], rule["close"])

        item["opening_hours"] = oh.as_opening_hours()

        apply_category(Categories.SHOP_INTERIOR_DECORATION, item)
        yield item
