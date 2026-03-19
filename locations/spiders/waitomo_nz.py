from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, FuelCards, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class WaitomoNZSpider(JSONBlobSpider):
    name = "waitomo_nz"
    start_urls = ["https://www.waitomogroup.co.nz/fuel-stop-finder"]
    item_attributes = {"brand": "Waitomo", "brand_wikidata": "Q112569504"}

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var stockists = ")]/text()').get()
        )
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["OPENINGSOON"] == "1":
            return
        apply_category(Categories.FUEL_STATION, item)

        item["ref"] = feature["REFTITLE"]
        item["opening_hours"] = OpeningHours()
        if feature["ALLTIME"] == "1":
            item["opening_hours"] = "24/7"
        else:
            for days in DAYS_FULL:
                if rule := feature[days.upper()]:
                    if rule == "24 HOURS":
                        item["opening_hours"].add_range(days, "00:00", "24:00")
                    elif rule == "CLOSED":
                        item["opening_hours"].set_closed(days)
                    else:
                        start_time, end_time = rule.split("-")
                        item["opening_hours"].add_range(days, start_time, end_time)

        apply_yes_no(Fuel.DIESEL, item, feature["DIESEL"] == "1")
        apply_yes_no(Fuel.OCTANE_91, item, feature["UNLEADED91"] == "1")
        apply_yes_no(Fuel.OCTANE_95, item, feature["PREMIUM95"] == "1")
        # typo of GoClear, local brand of DEF
        apply_yes_no(Fuel.ADBLUE, item, feature["GLCLEAR"] == "1")
        apply_yes_no(Fuel.ELECTRIC, item, feature["EV"] == "1")
        apply_yes_no(Fuel.LH2, item, feature["HYDROGEN"] == "1")

        apply_yes_no(Extras.CAR_WASH, item, feature["CARWASH"] == "1")

        apply_yes_no(FuelCards.MOBIL, item, feature["MOBILCARD"] == "1")

        yield item
