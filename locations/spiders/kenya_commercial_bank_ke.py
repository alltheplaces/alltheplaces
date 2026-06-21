from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KenyaCommercialBankKESpider(JSONBlobSpider):
    name = "kenya_commercial_bank_ke"
    item_attributes = {"brand": "KCB", "brand_wikidata": "Q7193999"}
    start_urls = ["https://ke.kcbgroup.com/api/branches"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.BANK, item)

        item.pop("email")
        item.pop("phone")

        item["branch"] = item.pop("name").removeprefix("KCB ")

        try:
            item["opening_hours"] = self.parse_opening_hours(feature.get("working_hours", ""))
        except Exception as e:
            self.logger.error(f'Error parsing opening hours for {feature.get("working_hours")}: {e}')
        yield item

    def parse_opening_hours(self, hours: str) -> OpeningHours | None:
        if not hours:
            return None
        opening_hours = OpeningHours()
        for rule in hours.split("\n"):
            day, times = rule.split(":")

            day = day.lower().replace("and public holidays", "")
            times = times.replace("noon", "pm")

            for result in OpeningHours.extract_hours_from_string(f"{day} {times}"):
                opening_hours.add_days_range(result[0], result[1], result[2])

        return opening_hours
