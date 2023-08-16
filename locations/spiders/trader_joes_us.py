from locations.hours import DAYS, OpeningHours
from locations.storefinders.where2getit import Where2GetItSpider


class TraderJoesUSSpider(Where2GetItSpider):
    name = "trader_joes_us"
    item_attributes = {"brand": "Trader Joe's", "brand_wikidata": "Q688825"}
    api_brand_name = "traderjoes"
    api_key = "8559C922-54E3-11E7-8321-40B4F48ECC77"

    def parse_item(self, item, location):
        item["website"] = (
            "https://locations.traderjoes.com/"
            + item["state"].lower()
            + "/"
            + item["city"].lower().replace(" ", "-")
            + "/"
            + item["ref"]
            + "/"
        )
        hours_string = ""
        for day_abbrev, day in zip(["mon", "tues", "wed", "thurs", "fri", "sat", "sun"], DAYS):
            if location.get(day_abbrev + "open") and location.get(day_abbrev + "close"):
                hours_string = (
                    f"{hours_string} {day}: " + location[day_abbrev + "open"] + "-" + location[day_abbrev + "close"]
                )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)
        yield item
