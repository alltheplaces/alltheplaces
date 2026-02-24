from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Extras, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChangeGroupSpider(JSONBlobSpider):
    name = "change_group"
    item_attributes = {"brand": "Change Group", "brand_wikidata": "Q5071758"}
    start_urls = ["https://uk.changegroup.com/dam/changegroup-mdm/branches.json"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("Forex"))
        feature.update(feature.pop("Localizacion")[0])

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["codBranch"]
        item["street_address"] = feature["direccion1"]
        item["postcode"] = feature["codPostal"]

        if hours := feature.get("Horario"):
            try:
                item["opening_hours"] = self.parse_opening_hours(hours[0])
            except:
                self.logger.error("Failed to parse opening hours {}".format(hours))

        apply_yes_no(Extras.ATM, item, feature.get("Servicios", {}).get("ATM"))
        yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in DAYS_FULL:
            open_time, close_time = [
                rules[f"{day.lower()}{t}"].replace(".", ":").replace("h", ":").strip() for t in ["Open", "Close"]
            ]
            if any(hours_text in open_time for hours_text in ["24 Hours", "Open 24H", "Öppet i sa"]):
                open_time, close_time = ("00:00", "23:59")
            opening_hours.add_range(day, open_time, close_time)
        return opening_hours
