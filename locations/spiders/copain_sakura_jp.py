import re
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import apply_category
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

BRAND = "こぱんはうすさくら"
DAYS_KANJI = "月火水木金土日"
TIME_RANGE_RE = re.compile(r"(\d{1,2}:\d{2})\s*[~～〜]\s*(\d{1,2}:\d{2})")


class CopainSakuraJPSpider(CrawlSpider):
    name = "copain_sakura_jp"
    item_attributes = {"brand": BRAND}
    allowed_domains = ["copain-sakura.com"]
    # The list page with an empty search shows every classroom.
    start_urls = ["https://copain-sakura.com/school/?area=&s="]
    rules = [Rule(LinkExtractor(allow=r"/school/\d+/$"), callback="parse_school")]

    def parse_school(self, response: Response) -> Iterable[Feature]:
        title = response.xpath("//h1/text()").get("").strip()
        # The finder also lists consultation offices (相談支援) under other
        # names. Only the classrooms carry the brand name.
        if not title.startswith(BRAND):
            return
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url
        item["name"] = BRAND
        item["branch"] = title.removeprefix(BRAND).strip()

        address = self.info_row(response, "所在地").xpath("./p/text()").get("").strip()
        # Some postcodes use other dash characters, e.g. "〒300ｰ0813".
        if m := re.match(r"〒\s*(\d{3})\D(\d{4})\s*(.+)", address):
            item["postcode"] = f"{m.group(1)}-{m.group(2)}"
            address = m.group(3)
        item["addr_full"] = address

        if src := self.info_row(response, "所在地").xpath(".//iframe/@src").get():
            # The Google Maps embed is centred a little west of the classroom's
            # pin, by about 7% of the map span ("!1d", in metres). Street level
            # embeds land within a few hundred metres. Wider ones are flagged
            # so that the point can be checked before it is used.
            if m := re.search(r"!1d([\d.]+)!2d(-?[\d.]+)!3d(-?[\d.]+)", src):
                item["lon"], item["lat"] = m.group(2), m.group(3)
                if float(m.group(1)) >= 5000:
                    item["extras"]["fixme"] = "low precision coordinates"

        tel = self.info_row(response, "電話番号")
        if "開所前" in tel.get(""):  # not open yet
            return
        item["phone"] = tel.xpath('.//a[starts-with(@href, "tel:")]/text()').get()
        item["opening_hours"] = self.parse_hours([line.strip() for line in tel.xpath("./text()").getall()])

        apply_category({"amenity": "social_facility", "social_facility": "day_care"}, item)
        item["extras"]["social_facility:for"] = "child"

        yield item

    @staticmethod
    def info_row(response: Response, heading: str):
        return response.xpath(
            f'//div[@class="school-info__table"]/div[@class="row"][normalize-space(div[@class="heading"])="{heading}"]'
            '/div[@class="content"]'
        )

    @staticmethod
    def parse_days(label: str) -> list[str] | None:
        # Public holidays are left out, opening_hours here has no PH rules.
        label = re.sub(r"[\s・、]", "", label)  # also drops "祝　日" spacing
        label = re.sub(r"開所日[:：]|曜日|曜|祝日|祝|長期休暇", "", label)
        days = []
        if "平日" in label:
            days += DAYS_WEEKDAY
            label = label.replace("平日", "")
        for start, end in re.findall(rf"([{DAYS_KANJI}])[~～〜]([{DAYS_KANJI}])", label):
            days += DAYS[DAYS_KANJI.index(start) : DAYS_KANJI.index(end) + 1]
        label = re.sub(rf"[{DAYS_KANJI}][~～〜][{DAYS_KANJI}]", "", label)
        for char in label:
            if char not in DAYS_KANJI:
                return None  # unknown label, e.g. "学校休業日"
            days.append(DAYS[DAYS_KANJI.index(char)])
        return days

    def parse_hours(self, lines: list[str]) -> OpeningHours | None:
        oh = OpeningHours()
        lines = [line.replace("：", ":") for line in lines if line]
        notes = [line for line in lines if line.startswith(("※", "（", "休所日"))]
        if any("のみ営業" in note for note in notes):
            return None  # e.g. "only open on the first Sunday"
        if any(re.search(r"\d{1,2}:\d{2}", note) for note in notes):
            return None  # e.g. a lunch break on its own line "（13:00～14:00除く）"
        closed = {"Su"} if any("日曜" in n and ("定休" in n or "休み" in n) for n in notes) else set()
        for line in lines:
            if line in notes or "定休日" in line:
                continue
            if not (m := TIME_RANGE_RE.search(line)):
                return None
            if line[m.end() :].strip(" \u3000"):
                return None  # e.g. a lunch break "（13:00～14:00除く）"
            label = line[: m.start()].strip(" \u3000")
            days = self.parse_days(label)
            if days is None or not label:
                return None
            if not days:
                continue  # public holidays only
            oh.add_days_range([d for d in days if d not in closed], m.group(1), m.group(2))
        return oh if oh.as_opening_hours() else None
