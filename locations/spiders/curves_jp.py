import re
from datetime import date
from typing import Iterable

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_WEEKDAY, OpeningHours
from locations.items import Feature


class CurvesJPSpider(Spider):
    name = "curves_jp"
    item_attributes = {"brand": "カーブス", "brand_wikidata": "Q5196080"}
    allowed_domains = ["www.curves.co.jp"]
    start_urls = ["https://www.curves.co.jp/search/shops.json"]

    def parse(self, response: Response) -> Iterable[Feature]:
        transformer = Transformer.from_pipeline("EPSG:15484")
        for shop in response.json():
            # Upcoming clubs carry the opening date in the name,
            # e.g. "大塚駅前 ＜2026年10月13日オープン＞" or "町田三和小川 ＜2027年オープン予定＞"
            branch, _, notice = shop["name"].partition("＜")
            if "予定" in notice or self.opens_later(shop["openday"]):
                continue

            item = Feature()
            item["ref"] = shop["url"].rsplit("/", 1)[-1].removesuffix(".php")
            item["branch"] = branch.strip()
            # The coordinates are in the Tokyo datum, about 450 m off from WGS 84
            item["lat"], item["lon"] = transformer.transform(float(shop["lat"]), float(shop["long"]))
            item["postcode"] = shop["zipcode"]
            item["state"] = shop["pref"]
            item["city"] = shop["city"]
            item["addr_full"] = shop["address"]
            item["phone"] = shop["tel"]
            item["website"] = response.urljoin(shop["url"])
            item["opening_hours"] = self.parse_hours(shop["bizhour"])
            # Curves clubs in Japan are for women only
            item["extras"]["female"] = "yes"
            item["extras"]["male"] = "no"
            apply_category(Categories.GYM, item)
            yield item

    @staticmethod
    def opens_later(openday: str) -> bool:
        # e.g. "2026/11/10"
        if m := re.fullmatch(r"(\d{4})/(\d{1,2})/(\d{1,2})", openday):
            return date(*map(int, m.groups())) > date.today()
        return False

    @staticmethod
    def parse_hours(bizhour: str) -> OpeningHours:
        # e.g. "平日：10:00-19:00(13:00-15:00はクローズ)<br>土曜：10:00-13:00"
        oh = OpeningHours()
        for line in bizhour.split("<br>"):
            if m := re.match(
                r"\s*(平日|土曜)：(\d{1,2}:\d{2})-(\d{1,2}:\d{2})(?:[（(](\d{1,2}:\d{2})-(\d{1,2}:\d{2})はクローズ[）)])?",
                line,
            ):
                days = DAYS_WEEKDAY if m.group(1) == "平日" else ["Sa"]
                open_time, close_time, break_start, break_end = m.groups()[1:]
                if break_start:
                    oh.add_days_range(days, open_time, break_start)
                    oh.add_days_range(days, break_end, close_time)
                else:
                    oh.add_days_range(days, open_time, close_time)
        return oh
