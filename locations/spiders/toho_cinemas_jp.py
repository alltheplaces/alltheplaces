import re
from typing import Iterable

import scrapy
from scrapy.http import Request, Response

from locations.categories import apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature

_PREFECTURES = {
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
}

_ASCII_RE = re.compile(r"^[A-Za-z0-9 ,.'\-]*$")


class TohoCinemasJPSpider(scrapy.Spider):
    name = "toho_cinemas_jp"
    item_attributes = {"brand": "TOHOシネマズ", "brand_wikidata": "Q11235261"}

    start_urls = ["https://www.tohotheater.jp/theater/find.html"]

    def parse(self, response: Response) -> Iterable[Request]:
        # find.html lists each theater as a schedule link with its 3-digit code
        for href in response.xpath('//a[contains(@href, "/net/schedule/")]/@href').getall():
            if match := re.search(r"/net/schedule/(\d{3})/", href):
                yield response.follow(
                    f"/theater/{match.group(1)}/institution.html",
                    callback=self.parse_institution,
                    cb_kwargs={"schedule_url": href},
                )

    def parse_institution(self, response: Response, schedule_url: str) -> Iterable[Request | Feature]:
        # The theater name is in <h1 class="c-page_heading"><span class="sub">.
        name = response.css("h1.c-page_heading span.sub::text").get()
        if not name:
            # Closed theaters (their pages redirect to the homepage) yield nothing
            return
        code = re.search(r"/theater/(\d{3})/", response.url).group(1)

        item = Feature()
        item["ref"] = code
        item["name"] = None
        item["branch"] = name.removeprefix("TOHOシネマズ").strip()
        item["website"] = response.urljoin(schedule_url)

        self._apply_cinema_facilities(response, item)

        yield response.follow(
            f"/theater/{code}/access.html",
            callback=self.parse_access,
            cb_kwargs={"item": item},
        )

    def parse_access(self, response: Response, item: Feature) -> Iterable[Feature]:
        if addr := self._clean_address(response):
            item["addr_full"] = addr

        phone_text = "".join(
            response.xpath(
                '//li[contains(@class, "route__item")][h4[starts-with(normalize-space(), "電話番号")]]//text()'
            ).getall()
        )
        if phone_match := re.search(r"\d{2,4}-\d{3,4}-\d{4}", phone_text):
            item["phone"] = phone_match.group(0)

        extract_google_position(item, response)

        yield item

    @staticmethod
    def _apply_cinema_facilities(response: Response, item: Feature) -> None:
        # Omitted keys: TCX, 轟音シアター, プレミアムシアター, DOLBY VISION, DTS:X
        if not (about := response.xpath('//*[contains(@class, "about__screen")]')):
            return

        if screen_count := TohoCinemasJPSpider._screen_count(about):
            item["extras"]["screen"] = str(screen_count)

        if about.xpath('.//a[contains(@href, "/service/imax/")]'):
            apply_yes_no("cinema:IMAX", item, True)
        if about.xpath('.//a[contains(@href, "/service/mx4d/")]'):
            apply_yes_no("cinema:MX4D", item, True)
        if about.xpath('.//a[contains(normalize-space(.), "DOLBY ATMOS")]'):
            apply_yes_no("cinema:dolby_atmos", item, True)

        # ScreenX and Dolby Cinema appear as screen names in the table
        table_text = re.sub(r"\s+", " ", about.xpath("string(.)").get() or "")
        if "ScreenX" in table_text:
            apply_yes_no("cinema:screenx", item, True)
        if "ドルビーシネマ" in table_text:
            apply_yes_no("cinema:dolby_cinema", item, True)

    @staticmethod
    def _screen_count(about) -> int | None:
        # Prefer the authoritative "Nスクリーン" total row when present, falling
        # back to counting the individual screen rows.
        for td in about.xpath(".//td"):
            text = " ".join(td.xpath(".//text()").getall()).strip()
            if match := re.fullmatch(r"([\d,]+)スクリーン", text):
                return int(match.group(1).replace(",", ""))
        count = 0
        for row in about.xpath(".//tr"):
            first = " ".join(row.xpath(".//td[1]//text()").getall()).strip()
            if re.search(r"(SCREEN|CINEMA)\s*\d+", first) or "PREMIER" in first:
                count += 1
        return count or None

    @staticmethod
    def _clean_address(response: Response) -> str | None:
        # The 住所 (address) block is the only address source on the page. Some
        # theaters host several venues (本館/別館, or two <li> blocks) sharing one
        # code, and some repeat the address in English. Keep only the primary
        # venue's Japanese address: the first 住所 <li> and its first <p>.
        lis = response.xpath('//li[contains(@class, "route__item")][h4[normalize-space()="住所"]]')
        if not lis:
            return None
        segments = []
        for p in lis[0].xpath(".//p"):
            text = "".join(p.xpath(".//text()").getall()).strip().replace("\u3000", " ")
            # Drop duplicated English paragraphs
            if text and not _ASCII_RE.fullmatch(text):
                segments.append(text)
        if not segments:
            return None
        text = " ".join(segments)

        # Secondary venues sometimes sit in the same paragraph; cut before them.
        for marker in ("【別館", "[ 別館 ]", "＜スクリーン"):
            if marker in text:
                text = text.split(marker)[0]
                break

        # Strip venue/screen markers, parenthesized notes, and postal codes
        text = re.sub(r"【[^】]*】", " ", text)
        text = re.sub(r"\[[^]]*]", " ", text)
        text = re.sub(r"＜[^＞]*＞", " ", text)
        text = re.sub(r"（[^）]*）", " ", text)
        text = re.sub(r"〒\s*\d{3}-\d{4}", " ", text)
        text = re.sub(r"(?<![0-9-])\d{3}-\d{4}(?![\d-])", " ", text)
        text = re.sub(r"\s+\d{3,}$", "", text)  # stray trailing digits
        text = re.sub(r"\s+", " ", text).strip()

        # Fix incomplete address by prepending the prefecture (e.g. 056 福岡市, 084 豊島区).
        if text and not any(text.startswith(pref) for pref in _PREFECTURES):
            if match := re.search(r'<meta name="keywords" content="([^"]*)"', response.text):
                prefectures = [t.strip() for t in match.group(1).split(",") if t.strip() in _PREFECTURES]
                if prefectures:
                    text = prefectures[0] + text
        return text
