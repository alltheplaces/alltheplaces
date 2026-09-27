import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class NorthPacificBankJPSpider(MapionSpider):
    name = "north_pacific_bank_jp"
    item_attributes = {"brand": "北洋銀行", "brand_wikidata": "Q11402354"}
    allowed_domains = ["hokuyo.mapion.co.jp"]
    feature_url_template = "https://hokuyo.mapion.co.jp/b/hokuyo/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:

        item["name"] = "北洋銀行"
        item["branch"] = data.get("name").split("（")[0]
        item.set_tag("branch:ja-Hira", data.get("poi_name_yomi"))

        oh = OpeningHours()
        if data.get("kind") == "20":
            if week := data.get("atm_time"):
                self.add_hours(oh, DAYS_WEEKDAY, week)
            if holi := data.get("atm_holi"):
                self.add_hours(oh, DAYS_WEEKEND, holi)
            apply_category(Categories.ATM, item)
        else:
            handle_time = data.get("handle_time")
            self.add_hours(oh, DAYS_WEEKDAY, handle_time)
            if handle_time and "土日祝日も同じ時間" in handle_time:
                self.add_hours(oh, DAYS_WEEKEND, handle_time)
            oh_atm = OpeningHours()
            self.add_hours(oh_atm, DAYS_WEEKDAY, data.get("atm_time"))
            if holi := data.get("atm_holi"):
                self.add_hours(oh_atm, DAYS_WEEKEND, data.get("atm_holi"))
            if oh_atm:
                apply_yes_no(Extras.ATM, item, oh_atm)
                item.set_tag("opening_hours:atm", oh_atm.as_opening_hours())
            item.set_tag("branch:en", data.get("poi_name_en").removesuffix(" BRANCH").capitalize())
            if wheel := data.get("service_flg6"):
                apply_yes_no(Extras.WHEELCHAIR, item, wheel == "1")
            apply_category(Categories.BANK, item)
        if oh:
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def add_hours(oh: OpeningHours, days: list[str], time_range: str | None):
        if not time_range:
            return
        for segment in re.split(r"<br\s*/?>", time_range.replace("：", ":")):
            if hours := re.match(r"(\d{1,2}:\d{2})[~〜～](\d{1,2}:\d{2})", segment.strip()):
                open_time = f"{hours.group(1)}"
                close_time = f"{hours.group(2)}"
                oh.add_days_range(days, open_time, close_time)
