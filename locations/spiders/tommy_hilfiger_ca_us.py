from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_FULL
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class TommyHilfigerCAUSSpider(Where2GetItSpider):
    name = "tommy_hilfiger_ca_us"
    item_attributes = {"brand": "Tommy Hilfiger", "brand_wikidata": "Q634881"}
    api_endpoint = "https://stores.tommy.com/rest/getlist"
    api_key = "05D7DC22-D987-11E9-A0C5-022A407E493E"

    def parse_item(self, item: Feature, location: dict):
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        item["branch"] = item.pop("name", None)

        item["opening_hours"] = OpeningHours()
        for day_name in DAYS_FULL:
            open_key = "{}_open".format(day_name.lower())
            close_key = "{}_close".format(day_name.lower())
            if open_time := location.get(open_key):
                item["opening_hours"].add_range(day_name, location.get(open_key), location.get(close_key))

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
