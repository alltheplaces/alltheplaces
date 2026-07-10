from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class BankAustriaATSpider(JSONBlobSpider):
    name = "bank_austria_at"
    item_attributes = {"brand": "Bank Austria", "brand_wikidata": "Q697619"}
    start_urls = ["https://www.bankaustria.at/filialen/api/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def pre_process_data(self, feature: dict) -> None:
        feature["street_address"] = feature.pop("Street", None)
        feature["email"] = (feature.pop("Email", None) or "").strip(";")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("Type") == "4":
            apply_category(Categories.ATM, item)
        else:
            apply_category(Categories.BANK, item)
            apply_yes_no(Extras.ATM, item, "Geldausgabeautomat" in feature.get("Features", ""))
        try:
            oh = OpeningHours()
            for day in DAYS:
                hours_str = feature.get(day.lower())
                if not hours_str:
                    continue
                if hours_str.lower() == "geschlossen":
                    oh.set_closed(day)
                    continue
                for time_range in hours_str.split(", "):
                    parts = time_range.split(" - ")
                    if len(parts) == 2:
                        oh.add_range(day, parts[0].strip(), parts[1].strip(), time_format="%H.%M")
            item["opening_hours"] = oh
        except Exception as e:
            self.logger.error(f"Failed to parse opening hours: {e}")
        yield item
