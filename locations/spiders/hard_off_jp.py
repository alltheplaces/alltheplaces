import re
import unicodedata
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature

HARD_OFF = {"brand": "HARD･OFF", "brand_wikidata": "Q11327274"}
OFF_HOUSE = {"brand": "OFF･HOUSE", "brand_wikidata": "Q11327274"}
HOBBY_OFF = {"brand": "HOBBY･OFF", "brand_wikidata": "Q11337980"}
MODE_OFF = {"brand": "MODE･OFF"}

# Store type (CSS class of the logo in the store list) to brand and the name
# prefixes used in store titles, e.g. "ハードオフ楽器館16号狭山店".
STORE_TYPES = {
    "hard_off": (HARD_OFF, ["ハードオフ"]),
    "hard_gakki": (HARD_OFF, ["ハードオフ楽器館", "ハードオフ楽器STUDIO"]),
    "hard_pc": (HARD_OFF, ["ハードオフPC館"]),
    "kamerakan": (HARD_OFF, ["ハードオフカメラ館"]),
    "kougukan": (HARD_OFF, ["ハードオフ工具館"]),
    "off_house": (OFF_HOUSE, ["オフハウス"]),
    "outdoor": (OFF_HOUSE, ["アウトドア＆スポーツ", "アウトドア＆フィッシング"]),
    "hobby_off": (HOBBY_OFF, ["ホビーオフ"]),
    "hobby_toreka": (HOBBY_OFF, ["ホビーオフトレカ専門館"]),
    "mode_off": (MODE_OFF, ["モードオフ"]),
    "mode_off_vintage": (MODE_OFF, ["モードオフVINTAGE＆LUXURY"]),
    "garage_off": ({"brand": "GARAGE･OFF"}, ["ガレージオフ"]),
    "liquor_off": ({"brand": "LIQUOR･OFF"}, ["リカーオフ"]),
    # BOOK OFF franchise stores run by the HARD OFF group
    "book_off": ({"brand": "ブックオフ", "brand_wikidata": "Q893011"}, ["ブックオフ"]),
}


class HardOffJPSpider(Spider):
    name = "hard_off_jp"
    allowed_domains = ["www.hardoff.co.jp"]
    # All store types in Japan; overseas stores are listed on a separate page.
    start_urls = [
        "https://www.hardoff.co.jp/shop/list/?a=100&w=&t1=on&t2=on&t3=on&t4=on&t5=on&t6=on&t8=on&t12=on&t13=on&t14=on&t15=on&t31=on&t41=on&t81=on"
    ]

    def parse(self, response: Response) -> Iterable[Request]:
        for store in response.xpath('//ul[@class="store_list2"]/li/a'):
            # "閉店済み" closed, "開店準備中" not open yet
            if store.xpath('.//*[contains(@class, "icon_txt")][text()="閉店済み" or text()="開店準備中"]'):
                continue
            store_type = store.xpath('.//p[contains(@class, "store_list2_logo")]/@class').get().split()[-1]
            title = store.xpath('normalize-space(.//h3[@class="store_list2_ttl"])').get()
            if "ネット販売" in title:
                continue  # online sales warehouse
            yield response.follow(
                store.xpath("@href").get(),
                callback=self.parse_store,
                cb_kwargs={"store_type": store_type, "title": title},
            )
        if next_page := response.xpath('//a[@class="nextpostslink"]/@href').get():
            yield response.follow(next_page)

    def parse_store(self, response: Response, store_type: str, title: str) -> Iterable[Feature]:
        brand, prefixes = STORE_TYPES[store_type]
        item = Feature()
        item["ref"] = response.url.rsplit("=", 1)[-1]
        item["website"] = response.url
        item.update(brand)
        item["name"] = next((p for p in sorted(prefixes, key=len, reverse=True) if title.startswith(p)), prefixes[0])
        item["branch"] = title.removeprefix(item["name"]).removesuffix("店")

        address = self.cell(response, "所在地") or ""
        if m := re.match(r"〒\s*(\d{3}-\d{4})\s*(.+)", address):
            item["postcode"], item["addr_full"] = m.groups()
            if m := re.match(r"東京都|北海道|(?:京都|大阪)府|.{2,3}県", item["addr_full"]):
                item["state"] = m.group()
        item["phone"] = response.xpath('//a[@class="tel1"]/text()').get()
        # The only coordinates on the site are in the Google Maps link, e.g. "maps?q=43.094369,141.26038"
        if m := re.search(r"google\.com/maps\?q=(-?\d+\.\d+),(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()
        item["opening_hours"] = self.parse_hours(self.cell(response, "営業時間"), self.cell(response, "定休日"))

        if store_type == "liquor_off":
            apply_category(Categories.SHOP_ALCOHOL, item)
            item["extras"]["second_hand"] = "only"
        elif store_type != "book_off":
            apply_category(Categories.SHOP_SECOND_HAND, item)
        yield item

    @staticmethod
    def cell(response: Response, header: str) -> str | None:
        text = response.xpath(
            f'//div[contains(@class, "detail_table")]//th[text()="{header}"]/following-sibling::td[1]//text()'
        )
        value = " ".join(t.strip() for t in text.getall() if t.strip())
        return value or None

    @staticmethod
    def parse_hours(hours: str | None, closed: str | None) -> OpeningHours | None:
        # e.g. "10:00～20:00", "10:30（土日祝10:00）～19:30", "平日10:30～19:30 土日祝10:00～19:30"
        # Stores open every day except around New Year are kept, holiday hours are left out.
        if not hours or not closed:
            return None
        closed = unicodedata.normalize("NFKC", closed)
        if not re.fullmatch(r"年中無休.*|なし|元[旦日]|1月1日(休業)?|1月1日2日3日|年始.*", closed):
            return None
        hours = unicodedata.normalize("NFKC", hours).replace("～", "~").replace("〜", "~")
        # Drop notes on the buying counter, the app or year end, e.g. "※買取受付 18:30まで"
        hours = re.split(r"※|買取|〔", hours)[0].rstrip(" (")
        hours = re.sub(r"全日|\((?:全日|年末年始[^)]*|\d+月[^)]*)\)?", "", hours).strip()
        time = r"(\d{1,2}:\d{2})"
        to = r"\s*[~-]\s*"
        oh = OpeningHours()
        if m := re.fullmatch(rf"{time}{to}{time}", hours):
            oh.add_days_range(DAYS, *m.groups())
        elif m := re.fullmatch(rf"{time}\s*\(土日祝?\s*{time}\){to}{time}", hours):
            oh.add_days_range(DAYS_WEEKDAY, m[1], m[3])
            oh.add_days_range(DAYS_WEEKEND, m[2], m[3])
        elif m := re.fullmatch(rf"平日\s*{time}{to}{time}\s*土日祝日?\s*{time}{to}{time}", hours):
            oh.add_days_range(DAYS_WEEKDAY, m[1], m[2])
            oh.add_days_range(DAYS_WEEKEND, m[3], m[4])
        elif m := re.fullmatch(rf"{time}{to}{time}\s*\(平日\)\s*{time}{to}{time}\s*\(土日祝\)", hours):
            oh.add_days_range(DAYS_WEEKDAY, m[1], m[2])
            oh.add_days_range(DAYS_WEEKEND, m[3], m[4])
        else:
            return None
        return oh
