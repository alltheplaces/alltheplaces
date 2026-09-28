import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class MufjJPSpider(MapionSpider):
    name = "mufj_jp"
    item_attributes = {"brand": "三菱UFJ銀行", "brand_wikidata": "Q988284"}
    allowed_domains = ["map.bk.mufg.jp"]
    feature_url_template = "https://map.bk.mufg.jp/b/bk_mufg/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:

        item["name"] = "三菱UFJ銀行"
        item["branch"] = data.get("name").removeprefix("ATMコーナー").lstrip()
        if eng := data.get("poi_name_english"):
            item.set_tag("branch:en", eng.removesuffix("Branch").rstrip())
        if hira := data.get("poi_name_yomi"):
            item.set_tag("branch:ja-Hira", hira)

        oh = OpeningHours()
        if data.get("poi_type") == "10":
            self.add_hours(oh, DAYS_WEEKDAY, data.get("atm_hours_weekdays"))
            if atm_sat := data.get("atm_hours_saturday"):
                self.add_hours(oh, ["Sa"], atm_sat)
            if atm_sun := data.get("atm_hours_sunday"):
                self.add_hours(oh, ["Su"], atm_sun)
            apply_category(Categories.ATM, item)
        else:
            self.add_hours(oh, DAYS_WEEKDAY, data.get("hours_weekdays"))
            oh_atm = OpeningHours()
            self.add_hours(oh_atm, DAYS_WEEKDAY, data.get("atm_hours_weekdays"))
            if atm_sat := data.get("atm_hours_saturday"):
                self.add_hours(oh_atm, ["Sa"], atm_sat)
            if atm_sun := data.get("atm_hours_sunday"):
                self.add_hours(oh_atm, ["Su"], atm_sun)
            if oh_atm:
                apply_yes_no(Extras.ATM, item, oh_atm)
                item.set_tag("opening_hours:atm", oh_atm.as_opening_hours())
            apply_yes_no(Extras.WHEELCHAIR, item, data.get("diff_flag"))
            apply_yes_no(Extras.PARKING, item, data.get("parking_flag"))
            apply_yes_no(Extras.TOILETS_WHEELCHAIR, item, data.get("wheel_rest_flag"))
            apply_yes_no(Extras.TOILETS_OSTOMY, item, data.get("osto_flag"))
            apply_yes_no(Extras.ELEVATOR, item, data.get("elevator_flag"))
            apply_category(Categories.BANK, item)
        if oh:
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def add_hours(oh: OpeningHours, days: list[str], time_range: str | None):
        if not time_range:
            return
        for segment in re.split(r"<br\s*/?>", time_range):
            if hours := re.match(r"(\d{1,2}:\d{2})[~〜～](\d{1,2}:\d{2})", segment.strip()):
                open_time = f"{hours.group(1)}"
                close_time = f"{hours.group(2)}"
                oh.add_days_range(days, open_time, close_time)
