from typing import AsyncIterator, Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider


class AnzSpider(JSONBlobSpider):
    name = "anz"
    item_attributes = {"brand": "ANZ", "brand_wikidata": "Q714641"}
    locations_key = "Features"

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://data.nowwhere.com.au/v3.2/features/ANZ_GLOBAL_LOCATIONS?key=lX8QnCpUMT4pv37nCCSY11Kpo4jCt6Cm8sElH7bF&bbox=-180 -90,180 90&sortBy=distance&filter=atm=1 or branch=1",
            headers={"Referer": "https://www.anz.com.au/"},
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = feature["uuid"]
        item["street_address"] = item.pop("street")
        self.parse_opening_hours(item, feature)
        item["email"] = (
            (item.get("email") or "")
            .replace("Pacopscallcentre1@anz.com", "")
            .replace("(Samoa Help Desk) ccsamoa@anz.com", "")
            .replace("SamoaCallCentre@anz.com", "")
            .strip(" /")
        )

        if feature["active"] != "1":
            set_closed(item)

        if feature["branch"] == "1":
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, feature["atm"] == "1")
        elif feature["atm"] == "1":
            apply_category(Categories.ATM, item)

        yield item

    def parse_opening_hours(self, item: Feature, feature: dict) -> None:
        item["opening_hours"] = OpeningHours()
        for days in DAYS_3_LETTERS:
            if rule := feature["openhours_" + days.lower()]:
                if "closed" in rule.lower():
                    item["opening_hours"].set_closed(days)
                elif "24 hours" in rule.lower():
                    item["opening_hours"].add_range(days, "00:00", "24:00")
                elif rule == "24-Jul":
                    # gibberish value, do nothing
                    pass
                else:
                    rule = rule.replace(" - ", "-").replace(" am", "am").replace("am - ", "am-")
                    if len(rule.split("-")) == 2:
                        try:
                            open_time, close_time = rule.split("-")
                            if "." not in open_time and ":" not in open_time:
                                # 12h hour value and am/pm, i.e. 9am-5pm
                                item["opening_hours"].add_range(days, open_time, close_time, "%I%p")
                            elif "am" not in open_time.lower() and ":" in open_time:
                                # 24h hour and minute value, i.e. 9:30-13:30
                                item["opening_hours"].add_range(days, open_time, close_time, "%H:%M")
                            elif "am" in open_time.lower() and "." in open_time:
                                item["opening_hours"].add_range(days, open_time, close_time, "%I.%M%p")
                            else:
                                self.logger.warning("didn't parse: {}".format(rule))
                        except ValueError:
                            self.logger.warning("Error parsing opening hours: {}".format(rule))
                    else:
                        self.log("rule not made of 2 components: {}".format(rule))
