from locations.categories import Categories, Drink, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_FULL, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class TraderJoesUSSpider(Where2GetItSpider):
    name = "trader_joes_us"
    item_attributes = {"brand": "Trader Joe's", "brand_wikidata": "Q688825"}
    api_brand_name = "traderjoes"
    api_key = "8559C922-54E3-11E7-8321-40B4F48ECC77"
    api_filter = {"comingsoon": {"ne": "Yes"}}

    def pre_process_data(self, location):
        location.pop("location", None)  # Fix coordinate mis-detection

    def parse_item(self, item, location):
        if location["warehouse"] == "1":
            return

        apply_yes_no(Drink.BEER, item, location.get("beer") == "Yes")
        apply_yes_no(Drink.LIQUOR, item, location.get("liquor") == "Yes")
        apply_yes_no(Drink.WINE, item, location.get("wine") == "Yes")

        item["image"] = location.get("locationimage")
        item["branch"] = item.pop("name").removeprefix("Trader Joe's ")
        if item["ref"] in item["branch"]:
            item["branch"] = item["branch"][: item["branch"].find(" (")]  # remove ref

        if location.get("wineshop") == "1":
            apply_category(Categories.SHOP_ALCOHOL, item)

        oh = OpeningHours()
        for day_abbrev, day in zip(DAYS_FULL, DAYS):
            day_abbrev = day_abbrev.lower()
            open_time = location.get(day_abbrev + "_open")
            close_time = location.get(day_abbrev + "_close")
            if open_time and close_time:
                oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh

        yield item
