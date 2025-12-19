from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.stockist import StockistSpider


class ChampionSpider(StockistSpider):
    name = "champion"
    item_attributes = {"brand": "Champion", "brand_wikidata": "Q2948688"}
    key = "map_w3rk47yq"

    def parse_item(self, item: Feature, location: dict):
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for custom_field in location["custom_fields"]:
            if custom_field["name"] in DAYS_FULL:
                if custom_field["value"] == "-":
                    # Probably denotes unknown opening hours rather than
                    # closure on a particular day.
                    continue
                if custom_field["value"] == "x":
                    # Probably denotes a closed day.
                    item["opening_hours"].set_closed(DAYS_EN[custom_field["name"]])
                    continue
                if "," in custom_field["value"]:
                    for time_range in custom_field["value"].split(","):
                        item["opening_hours"].add_range(
                            DAYS_EN[custom_field["name"]], *time_range.strip().split(" - ", 1)
                        )
                else:
                    item["opening_hours"].add_range(
                        DAYS_EN[custom_field["name"]], *custom_field["value"].split(" - ", 1)
                    )
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
