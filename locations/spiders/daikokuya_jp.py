import json
import re
import unicodedata
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

TIME_RANGE = re.compile(r"(\d{1,2}:\d{2})\s*~\s*(\d{1,2}:\d{2})")
DAY_SPEC = re.compile(r"^[\s:]*([月火水木金土日祝平全曜・/、~]+)")
DAY_SPEC_END = re.compile(r"([月火水木金土日祝平全曜・/、~]+)[\s:]*$")
DAY_CHARS = {k[0]: v for k, v in DAYS_JP.items()}


class DaikokuyaJPSpider(LocationCloudSpider):
    name = "daikokuya_jp"
    item_attributes = {"brand": "大黒屋", "brand_wikidata": "Q11442068"}
    api_endpoint = "https://shop.e-daikoku.com/info/api/proxy2/shop/list"
    website_formatter = "https://shop.e-daikoku.com/info/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        item["branch"] = source_feature["name"].removeprefix("大黒屋 ")
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby.removeprefix("だいこくや ")
        if address_name := source_feature.get("address_name"):
            item["addr_full"] = re.sub(r"<\/?.*>", "", address_name)  # removes HTML
        if phone := source_feature.get("phone"):
            item["phone"] = phone

        apply_category(Categories.SHOP_PAWNBROKER, item)

        yield item

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        texts = {}
        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                texts.setdefault(text["label"], text["value"])

        if hours := texts.get("営業時間"):
            item["opening_hours"] = self.parse_opening_hours(hours, texts.get("休業日") or "")

        yield item

    @staticmethod
    def parse_days(spec: str) -> list[str]:
        spec = re.sub(r"祝祭日|祝日", "祝", spec).replace("曜日", "").replace("曜", "")
        days = []
        if "全日" in spec:
            days += DAYS
        if "平日" in spec:
            days += DAYS_WEEKDAY
            spec = spec.replace("平日", "")
        for start, end in re.findall(r"([月火水木金土日])~([月火水木金土日])", spec):
            days += DAYS[DAYS.index(DAY_CHARS[start]) : DAYS.index(DAY_CHARS[end]) + 1]
        spec = re.sub(r"[月火水木金土日]~[月火水木金土日]", "", spec)
        days += [DAY_CHARS[c] for c in spec if c in DAY_CHARS]
        return days

    def parse_opening_hours(self, hours: str, closed: str) -> OpeningHours:
        text = re.sub(r"\(※([月火水木金土日])\)", r"\1", unicodedata.normalize("NFKC", hours))
        text = re.sub(r"<[^>]+>", "", re.sub(r"<br\s*/?>|</p>|\(", "\n", text)).replace(")", "")
        ranges: dict[str, list[tuple[str, str]]] = {}
        for line in text.split("※")[0].splitlines():
            if re.search(r"受付|休憩|昼休|お知らせ|異なります|[A-Za-z]", line):
                continue
            matches = list(TIME_RANGE.finditer(line))
            if not matches:
                continue
            days_before = bool(DAY_SPEC_END.search(line[: matches[0].start()]))
            line_ranges = {}
            for i, match in enumerate(matches):
                if days_before:
                    spec = DAY_SPEC_END.search(line[matches[i - 1].end() if i else 0 : match.start()])
                else:
                    spec = DAY_SPEC.search(line[match.end() : matches[i + 1].start() if i + 1 < len(matches) else None])
                for day in (self.parse_days(spec.group(1)) if spec else []) or DAYS:
                    line_ranges.setdefault(day, []).append(match.groups())
            ranges.update(line_ranges)

        oh = OpeningHours()
        for day, times in ranges.items():
            for open_time, close_time in times:
                oh.add_range(day, open_time, close_time)

        # Weekly closing days only, not "第1月曜日", "隔週", "奇数月" or dates like "毎月7日" and "10/29(木)"
        closed = re.sub(r"<[^>]+>|\(.*?\)|\d+/\d+", "", unicodedata.normalize("NFKC", closed)).split("※")[0]
        closed = re.sub(
            r"(第[\d一二三四、,・. ]+|隔週|奇数月の第\d)[月火水木金土日]曜?日?|毎月[\d、, ]*日?", "", closed
        )
        if not re.search(r"\d", closed):
            for day in self.parse_days(closed):
                oh.set_closed(day)
        return oh
