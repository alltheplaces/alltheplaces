import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class ShizuokaBankJPSpider(MapionSpider):
    name = "shizuoka_bank_jp"
    item_attributes = {"brand": "静岡銀行", "brand_wikidata": "Q7499501"}
    allowed_domains = ["lbs.mapion.co.jp"]
    api_group = "new_shizuokabank"
    website_template = "https://sasp.mapion.co.jp/b/shizuokabank/info/{}/"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:

        item["name"] = "静岡銀行"
        item["branch"] = data.get("name")
        item.set_tag("branch:ja-Hira", data.get("poi_name_yomi"))
        if "お問い合わせ先" in (data.get("tel") or ""):
            item["phone"] = None

        oh = OpeningHours()
        if week := data.get("open_hour_week"):
            self.add_hours(oh, DAYS_WEEKDAY, week)
        if sat := data.get("open_hour_sat"):
            self.add_hours(oh, ["Sa"], sat)
        if sun := data.get("open_hour_sun"):
            self.add_hours(oh, ["Su"], sun)
        if data.get("store_div") == "3":
            if week := data.get("atm_hour_week"):
                self.add_hours(oh, DAYS_WEEKDAY, week)
            if sat := data.get("atm_hour_sat"):
                self.add_hours(oh, ["Sa"], sat)
            if sun := data.get("atm_hour_sun"):
                self.add_hours(oh, ["Su"], sun)
            apply_category(Categories.ATM, item)
        elif data.get("store_div") == "1":
            oh_atm = OpeningHours()
            if week := data.get("atm_hour_week"):
                self.add_hours(oh_atm, DAYS_WEEKDAY, week)
            if sat := data.get("atm_hour_sat"):
                self.add_hours(oh_atm, ["Sa"], sat)
            if sun := data.get("atm_hour_sun"):
                self.add_hours(oh_atm, ["Su"], sun)
            if oh_atm:
                apply_yes_no(Extras.ATM, item, oh_atm)
                atm_hours = oh_atm.as_opening_hours()
                item.set_tag("opening_hours:atm", atm_hours)
            item.set_tag("branch:en", data.get("poi_name_en").removesuffix(" BRANCH").capitalize())
            if wheel := data.get("wheelchair"):
                apply_yes_no(Extras.WHEELCHAIR, item, wheel == "1")
            apply_category(Categories.BANK, item)
        elif data.get("store_div") == "4":
            item["name"] = "静銀ティーエム証券"
            item["branch"] = data.get("name").removeprefix("静銀ティーエム証券")
            apply_category(Categories.OFFICE_FINANCIAL_ADVISOR, item)
        else:
            apply_category(Categories.OFFICE_FINANCIAL_ADVISOR, item)
        if oh:
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def add_hours(oh: OpeningHours, days: list[str], time_range: str | None):
        if not time_range:
            return
        for segment in re.split(r"<BR\s*/?>", time_range.replace("：", ":")):
            segment = segment.strip()
            if segment == "ご利用できません":
                oh.set_closed(days)
                continue
            if hours := re.match(r"(\d{1,2}:\d{2})[~〜～](\d{1,2}:\d{2})", segment):
                open_time = f"{hours.group(1)}"
                close_time = f"{hours.group(2)}"
                try:
                    oh.add_days_range(days, open_time, close_time)
                except:
                    pass
