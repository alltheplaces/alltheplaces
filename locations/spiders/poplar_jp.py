import re
import unicodedata

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS, DAYS_JP, OpeningHours
from locations.items import Feature

# 営業時間 (opening hours) values. A time range uses an ASCII hyphen, a
# full-width dash (－) or ～ between the open and close times, e.g.
# "7:00-1:00", "平日6:30－23:00、土日祝6:30‐22:00".
HOURS_RE = re.compile(r"(?P<open>\d{1,2}:\d{2})\s*[~～\-－‐]\s*(?P<close>\d{1,2}:\d{2})")

POSTCODE_RE = re.compile(r"〒(?P<postcode>\d{3}-\d{4})")

# The site mixes full-width (：０-９) and half-width time/digit glyphs.
FULLWIDTH = str.maketrans("０１２３４５６７８９：～", "0123456789:~")

# Weekday characters in the same order as hours.DAYS (Mo..Su).
WEEKDAYS = "月火水木金土日"

# brand strings per listing icon alt -> (brand, wikidata)
BRANDS = {
    "ポプラ": ("ポプラ", "Q7229380"),
    "生活彩家": ("生活彩家", "Q130741275"),
    "スリーエイト": ("スリーエイト", "Q7229380"),
}


class PoplarJPSpider(scrapy.Spider):
    name = "poplar_jp"
    allowed_domains = ["www.poplar-cvs.co.jp"]

    # The apex domain poplar-cvs.co.jp has no DNS record; only the www
    # subdomain resolves.
    start_urls = ["https://www.poplar-cvs.co.jp/shop_search/result2.php?keyword="]

    def parse(self, response: Response):
        for row in response.xpath('//table[contains(@class,"result_list")]//tr'):
            href = row.xpath("./td[1]/a/@href").get()
            if not href:
                continue
            detail_url = response.urljoin(href)

            brand_alt = row.xpath("./td[1]/img/@alt").get()
            brand_name, brand_wikidata = BRANDS.get(brand_alt, (brand_alt, None))

            store_name = row.xpath("./td[1]/a/@title").get() or ""
            store_name = " ".join(store_name.split())
            if not store_name:
                name_text = " ".join(row.xpath("./td[1]/a/text()").get("").split())
                store_name = name_text.replace(brand_name, "", 1).strip()

            addr_parts = row.xpath("./td[2]//text()").getall()
            addr_text = " ".join(" ".join(addr_parts).split())
            postcode = None
            if m := POSTCODE_RE.search(addr_text):
                postcode = m.group("postcode")
                addr_text = addr_text[m.end() :].strip()

            phone = " ".join(row.xpath("./td[3]//text()").getall()).strip()

            item = Feature()
            item["ref"] = href.rsplit("=", 1)[-1]
            item["name"] = brand_name
            item["branch"] = unicodedata.normalize("NFKC", store_name)
            item["brand"] = brand_name
            if brand_wikidata:
                item["brand_wikidata"] = brand_wikidata
            item["addr_full"] = unicodedata.normalize("NFKC", addr_text)
            if postcode:
                item["postcode"] = postcode
            if phone:
                item["phone"] = f"+81 {phone}"
            item["country"] = "JP"
            item["website"] = detail_url

            apply_category(Categories.SHOP_CONVENIENCE, item)

            yield scrapy.Request(detail_url, callback=self.parse_store, cb_kwargs={"item": item})

        # Page navigation appears in both a top and bottom block, each with a
        # "前へ" (prev) and "次へ" (next) link. Follow the "next" link only,
        # otherwise the first match on page 2 is the prev link (page 1),
        # looping forever.
        next_page = response.xpath('//a[@class="page_navi" and contains(text(),"次へ")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_store(self, response: Response, item: Feature):
        # Each store detail page embeds a Google Maps iframe (either the
        # embed?pb= form or maps.google.co.jp/maps?q={lat},{lon}) carrying the
        # store marker; extract the coordinates from it.
        extract_google_position(item, response)

        hours_text = " ".join(
            response.xpath('//th[contains(text(),"営業時間")]/following-sibling::td[1]//text()').getall()
        ).strip()
        closed_text = " ".join(
            response.xpath('//th[contains(text(),"休業日")]/following-sibling::td[1]//text()').getall()
        ).strip()

        if opening_hours := self.parse_hours(hours_text, closed_text):
            item["opening_hours"] = opening_hours.as_opening_hours()

        yield item

    @classmethod
    def parse_hours(cls, hours_text: str, closed_text: str) -> OpeningHours | None:
        if not hours_text:
            return None

        # Normalise full-width glyphs, drop <br>, and ignore explanatory
        # notes (introduced by ※ or ただし) which describe partial or
        # self-checkout hours rather than the regular schedule.
        text = hours_text.translate(FULLWIDTH)
        text = re.sub(r"<br\s*/?>", " ", text)
        text = re.split(r"※|ただし", text)[0]

        closed = cls.closed_weekdays(closed_text)

        oh = OpeningHours()
        # 24時間 = open round the clock every day.
        if "24時間" in text:
            oh.add_days_range(DAYS, "00:00", "23:59")
        else:
            # The text is a sequence of "<day label> <open>-<close>" groups,
            # each optionally carrying a day label (平日 / 月-金 / 土日祝 / ...).
            # Iterate every time range and use the text since the previous range
            # as its day label, so multiple groups on one line are all captured.
            previous = 0
            for m in HOURS_RE.finditer(text):
                label = text[previous : m.start()]
                previous = m.end()
                for day in cls.day_group(label):
                    oh.add_range(day, m.group("open"), m.group("close"))

        for day in closed:
            oh.set_closed(day)

        return oh

    @staticmethod
    def day_group(label: str) -> list[str]:
        """Map a Japanese day label to hours.DAYS codes, defaulting to all
        days when the label is empty. Holiday-only labels (e.g. 祝) carry no
        weekday and are dropped rather than wrongly applied to every day.
        hours_text is not well-structured so this is best-effort parsing.
        """
        label = label.translate(FULLWIDTH)
        if not label:
            return DAYS
        if not re.search(rf"[{WEEKDAYS}]", label):
            return []
        if "平日" in label:
            return DAYS[:5]
        if "週末" in label:
            return DAYS[5:]
        cleaned = re.sub(r"[祝(（).、\s]", "", label)
        days = []
        for group in re.split(r"[・/]", cleaned):
            if not group:
                continue
            if m := re.match(rf"([{WEEKDAYS}])[-~]([{WEEKDAYS}])", group):
                start, end = WEEKDAYS.index(m.group(1)), WEEKDAYS.index(m.group(2))
                if start <= end:
                    days.extend(WEEKDAYS[start : end + 1])
                else:
                    days.extend(WEEKDAYS[start:] + WEEKDAYS[: end + 1])
            else:
                days.extend(ch for ch in group if ch in WEEKDAYS)
        return [DAYS_JP[d] for d in days]

    @staticmethod
    def closed_weekdays(closed_text: str) -> list[str]:
        # 年中無休 = no regular weekly closure.
        if not closed_text or "年中無休" in closed_text:
            return []
        # Keep only the leading part of the text up to the first closure note
        # (facility / summer / year-end / school / hospital ...). The weekly
        # closure is stated before such occasional notes, which must not leak
        # their weekday tokens (e.g. 夏季休業...火曜日、水曜日、木曜日) into
        # the regular closing schedule.
        note_words = (
            "休業",
            "年始",
            "年末",
            "夏季",
            "冬季",
            "指定日",
            "休館",
            "お盆",
            "学校",
            "大学",
            "病院",
            "施設",
            "不定",
            "程度",
            "最終",
            "お休み",
            "毎月",
        )
        primary = re.split("|".join(note_words), closed_text)[0]
        # Drop rank-based closures (第N曜日: the Nth weekday of the month).
        primary = re.sub(r"第[0-9.,、\s]*[月火水木金土日]曜日", "", primary)
        closed = set()
        # 土日 (contiguous) means closed all weekend.
        if re.search(r"土日", primary):
            closed.update(["Sa", "Su"])
        else:
            if re.search(r"土・日|土曜", primary):
                closed.add("Sa")
            if re.search(r"日・祝|日祝", primary):
                closed.add("Su")
            # A standalone 日 (not part of 日祝/日曜日) means Sunday.
            if re.search(r"(?<![土日月火水木金祝曜])日(?![祝曜])", primary):
                closed.add("Su")
        for m in re.finditer(r"[月火水木金土日]曜日", primary):
            closed.add(DAYS_JP[m.group(0)[0]])
        return list(closed)
