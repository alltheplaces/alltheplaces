import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class ChibaBankJPSpider(MapionSpider):
    name = "chiba_bank_jp"
    item_attributes = {"brand": "千葉銀行", "brand_wikidata": "Q1071712"}
    allowed_domains = ["sasp.mapion.co.jp"]
    feature_url_template = "https://sasp.mapion.co.jp/b/chibabank/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:

        item["name"] = "千葉銀行"
        item["branch"] = data.get("name")

        oh = OpeningHours()
        if data.get("store_kind") == "2":
            self.add_hours(oh, DAYS_WEEKDAY, data.get("week_atm").replace("：", ":"))
            self.add_hours(oh, ["Sa"], data.get("sat_atm").replace("：", ":"))
            self.add_hours(oh, ["Su"], data.get("sun_atm").replace("：", ":"))
            apply_category(Categories.ATM, item)
        elif data.get("store_kind") == "0":  # foreign exchange counter, no opening hours in data.
            item.set_tag("branch:ja-Hira", data.get("poi_name_yomi").removeprefix("（").removesuffix("）"))
            apply_category(Categories.BUREAU_DE_CHANGE, item)
        else:
            self.add_hours(oh, DAYS_WEEKDAY, data.get("week_time").replace("：", ":"))
            self.add_hours(oh, DAYS_WEEKEND, data.get("holi_time").replace("：", ":"))
            oh_atm = OpeningHours()
            self.add_hours(oh_atm, DAYS_WEEKDAY, data.get("week_atm").replace("：", ":"))
            self.add_hours(oh_atm, ["Sa"], data.get("sat_atm").replace("：", ":"))
            self.add_hours(oh_atm, ["Su"], data.get("sun_atm").replace("：", ":"))
            if oh_atm:
                apply_yes_no(Extras.ATM, item, oh_atm)
                item.set_tag("opening_hours:atm", oh_atm.as_opening_hours())
            item.set_tag("branch:ja-Hira", data.get("poi_name_yomi").removeprefix("（").removesuffix("）"))
            item.set_tag("branch:en", data.get("poi_name_yomi_en").removesuffix(" Branch"))
            apply_yes_no(Extras.WHEELCHAIR, item, data.get("wheelchair_flg") == "1")
            apply_yes_no(Extras.PARKING, item, data.get("parking_flg") == "1")
            apply_category(Categories.BANK, item)
        if oh:
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def add_hours(oh: OpeningHours, days: list[str], time_range: str | None):
        if not time_range:
            return
        monday_time_range = None
        if "Mo" in days and (match := re.search(r"※月曜日は(.+)", time_range)):
            monday_time_range = match.group(1)
            time_range = time_range[: match.start()]
            days = [day for day in days if day != "Mo"]
        for segment in re.split(r"<br\s*/?>", time_range):
            if hours := re.match(r"(\d{1,2}):(\d{2})[~〜～](\d{1,2}):(\d{2})", segment.strip()):
                # Some ATMs use "25:00" style times to mean 01:00 the next
                # day; normalise so OpeningHours' own overnight handling
                # (triggered when close < open) picks it up.
                open_time = f"{int(hours.group(1)) % 24:02d}:{hours.group(2)}"
                close_hour = int(hours.group(3))
                if close_hour == 24 and hours.group(4) == "00":
                    close_time = "24:00"
                else:
                    close_time = f"{close_hour % 24:02d}:{hours.group(4)}"
                oh.add_days_range(days, open_time, close_time)
        if monday_time_range:
            ChibaBankJPSpider.add_hours(oh, ["Mo"], monday_time_range)
