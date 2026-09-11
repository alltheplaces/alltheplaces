import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.subway import SubwaySpider


class SubwayTWSpider(JSONBlobSpider):
    name = "subway_tw"
    item_attributes = SubwaySpider.item_attributes
    start_urls = ["https://www.subway.com.tw/stores-data.json"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = feature["storeNum"]
        item["opening_hours"] = self.parse_hours(feature["hours"])
        apply_category(Categories.FAST_FOOD, item)
        apply_yes_no(PaymentMethods.LINE_PAY, item, "LinePay" in feature["payment"], False)
        item["extras"]["cuisine"] = "sandwich"
        item["extras"]["takeaway"] = "yes"
        yield item

    @staticmethod
    def parse_hours(hours: str) -> OpeningHours:
        opening_hours = OpeningHours()
        if all_week := re.match(r"\s*(\d{1,2}:\d{2})\s*[-~]\s*(\d{1,2}:\d{2})", hours):
            # A leading range with no day prefix covers the whole week, one store then adds weekend hours
            opening_hours.add_days_range(DAYS, all_week.group(1), all_week.group(2))
            hours = hours[all_week.end() :]
        opening_hours.add_ranges_from_string(hours, delimiters=["-", "~"], closed=["未營業"])
        if days_off := re.search(r"((?:[A-Z]{3}[,\s]+)*[A-Z]{3}) day off", hours):
            opening_hours.set_closed([sanitise_day(day) for day in re.findall(r"[A-Z]{3}", days_off.group(1))])
        return opening_hours
