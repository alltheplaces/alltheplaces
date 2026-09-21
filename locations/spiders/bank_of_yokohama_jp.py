import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, DAYS_WEEKDAY
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class BankOfYokohamaJPSpider(MapionSpider):
    name = "bank_of_yokohama_jp"
    item_attributes = {"brand": "横浜銀行", "brand_wikidata": "Q2744340"}
    allowed_domains = ["sasp.mapion.co.jp"]
    feature_url_template = "https://sasp.mapion.co.jp/b/boy/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        
        item["name"] = "横浜銀行"
        item["branch"] = data.get("name")

        oh = OpeningHours()
        if data.get("kind") == "ATMコーナー":
            # A standalone ATM corner, not a staffed branch: use the ATM's
            # own hours, which can differ between weekdays and weekends.
            self.add_hours(oh, DAYS_WEEKDAY, data.get("atm_time"))
            self.add_hours(oh, ["Sa"], data.get("atm_sat"))
            self.add_hours(oh, ["Su"], data.get("atm_sun"))
            apply_category(Categories.ATM, item)
        else:
            # "handle_time" is the teller counter's opening hours, e.g.
            # "9:00～11:30<br/>12:30～15:00" for branches with a lunch
            # closure. Transfer-only branches have no counter and so no
            # handle_time, leaving opening_hours blank.
            self.add_hours(oh, DAYS_WEEKDAY, data.get("handle_time"))
            apply_category(Categories.BANK, item)
        if oh:
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def add_hours(oh: OpeningHours, days: list[str], time_range: str | None):
        if not time_range:
            return
        for segment in re.split(r"<br\s*/?>", time_range):
            if hours := re.match(r"(\d{1,2}):(\d{2})[~〜～](\d{1,2}):(\d{2})", segment.strip()):
                # Some ATMs use "25:00" style times to mean 01:00 the next
                # day; normalise so OpeningHours' own overnight handling
                # (triggered when close < open) picks it up.
                open_time = f"{int(hours.group(1)) % 24:02d}:{hours.group(2)}"
                close_time = f"{int(hours.group(3)) % 24:02d}:{hours.group(4)}"
                oh.add_days_range(days, open_time, close_time)
