import re
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, OpeningHours
from locations.items import Feature


class KaraokeBanbanJPSpider(Spider):
    name = "karaoke_banban_jp"
    item_attributes = {"brand": "カラオケバンバン", "brand_wikidata": "Q88485685"}
    allowed_domains = ["karaoke-shin.jp"]
    start_urls = [f"https://karaoke-shin.jp/shop-area/{pref:02}.html" for pref in range(1, 48)]

    def parse(self, response: Response) -> Iterable[Request]:
        for shop in response.xpath('//div[@class="shopname"]'):
            name = shop.xpath("normalize-space(a)").get()
            # The operator also lists its other karaoke chains (カラオケALL,
            # カラオケアメリカンドリーム, ...) on the same pages
            if not name.startswith("カラオケBanBan"):
                continue
            url = shop.xpath("a/@href").get()
            details = shop.xpath('following-sibling::div[@id="sss"][1]')

            item = Feature()
            item["ref"] = url.rsplit("/", 1)[-1].removesuffix(".html")
            item["website"] = url
            item["name"] = self.item_attributes["brand"]
            item["branch"] = name.removeprefix("カラオケBanBan").removesuffix("店")
            item["phone"] = details.xpath('a[starts-with(@href, "tel:")]/text()').get()

            lines = [line.strip() for line in details.xpath("text()").getall() if line.strip()]
            if lines and (m := re.match(r"〒(\d{3}-\d{4})\s*(.+)", lines[0])):
                item["postcode"], item["addr_full"] = m.groups()
            item["opening_hours"] = self.parse_hours(details.xpath("normalize-space(td)").get())

            apply_category(Categories.KARAOKE_BOX, item)
            yield response.follow(url, callback=self.parse_coordinates, cb_kwargs={"item": item})

    def parse_coordinates(self, response: Response, item: Feature) -> Iterable[Feature]:
        # The Google Maps embed is centred on the shop, e.g. "&center=35.725976,140.65718"
        if src := response.xpath('//div[@class="ggmap"]/iframe/@src').get():
            if m := re.search(r"center=(-?[\d.]+),(-?[\d.]+)", src):
                item["lat"], item["lon"] = m.groups()
        yield item

    @staticmethod
    def parse_hours(text: str | None) -> OpeningHours | None:
        # e.g. "10:00～翌5:00", "24H", "10:00（土・日・祝 9:00）～翌3:00（金・土・祝前 翌5:00）"
        # Holiday and day-before-holiday variations are left out.
        if not text:
            return None
        text = text.replace("：", ":").replace("(", "（").replace(")", "）")
        oh = OpeningHours()
        if text == "24H":
            oh.add_days_range(DAYS, "00:00", "24:00")
            return oh
        m = re.fullmatch(
            r"(\d{1,2}:\d{2})(?:（土・日・祝\s*(\d{1,2}:\d{2})）)?～翌?(\d{1,2}:\d{2})"
            r"(?:（([月火水木金土日曜・祝前のみ]+?)\s*は?\s*翌(\d{1,2}:\d{2})）)?",
            text,
        )
        if not m:
            return None
        open_time, weekend_open, close_time, late_days, late_close = m.groups()
        # e.g. "金・土・祝前" (Fri, Sat and days before holidays), "土曜日", "土のみ"
        late = [DAYS_JP[c] for c in (late_days or "").replace("曜日", "") if c in DAYS_JP]
        for day in DAYS:
            day_open = weekend_open if weekend_open and day in ("Sa", "Su") else open_time
            day_close = late_close if day in late else close_time
            hours, minutes = day_close.split(":")
            oh.add_range(day, day_open, f"{int(hours) % 24:02d}:{minutes}")
        return oh
