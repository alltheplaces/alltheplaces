import re
from typing import Iterable
from urllib.parse import urlparse

from scrapy.http import Response
from scrapy.spiders import SitemapSpider, Spider

from locations.categories import Categories, Extras, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours, day_range
from locations.items import Feature


class KrispyKremeJPSpider(SitemapSpider, Spider):
    name = "krispy_kreme_jp"
    allowed_domains = ["krispykreme.jp"]
    start_urls = ["https://krispykreme.jp"]
    item_attributes = {"brand": "Krispy Kreme", "brand_wikidata": "Q1192805", "extras": Categories.FAST_FOOD.value}
    sitemap_urls = ["https://krispykreme.jp/store-sitemap.xml"]

    # third-party delivery providers shown in the 外部サービス block:
    # page label -> trade name (delivery:partner) and wikidata id
    DELIVERY_PARTNERS = {
        "Uber Eats": "Uber Eats",
        "出前館": "Demae-can",
        "Too Good To Go": "Too Good To Go",
        "menu": "menu",
        "Rocket Now": "Rocket Now",
    }
    DELIVERY_PARTNERS_WIKIDATA = {
        "Uber Eats": "Q21462723",
        "出前館": "Q11395551",
        "Too Good To Go": "Q85810097",
        "menu": "Q140478792",
        # Rocket Now has no wikidata item
    }

    def parse(self, response: Response) -> Iterable[Feature]:
        store_detail = response.xpath('//div[@class="store_detail"]')
        if not store_detail:
            # /store/ index page and other non-store pages have no detail block
            return
        info_col = store_detail.xpath('.//div[contains(concat(" ", normalize-space(@class), " "), " info_col ")]')

        item = Feature()
        # no store id found, so use URL parts as ID: pref + '-' + store-name-slug
        #   /store/tokyo/meiji-jingumae.html -> "tokyo-meiji-jingumae"
        #   /store/kanagawa/atre_kawasaki_northgate.html -> "kanagawa-atre-kawasaki-northgate"
        parts = urlparse(response.url).path.rstrip("/").split("/")
        item["ref"] = f"{parts[-2]}-{parts[-1].removesuffix('.html')}".replace("_", "-")
        item["website"] = response.url
        item["lat"] = store_detail.xpath('.//div[contains(@class, "marker")]/@data-lat').get()
        item["lon"] = store_detail.xpath('.//div[contains(@class, "marker")]/@data-lng').get()
        item["branch"] = info_col.xpath('.//div[contains(@class, "pc_disp")]/h3[1]/text()').get()
        item["extras"]["branch:en"] = info_col.xpath('.//div[contains(@class, "pc_disp")]/h3[2]/text()').get().strip()
        item["addr_full"] = info_col.xpath('.//dt[text()="住所"]/following-sibling::dd/text()').get()
        item["phone"] = info_col.xpath(
            './/dt[text()="電話番号"]/following-sibling::dd//span[contains(@class, "tel")]/text()'
        ).get()

        if seats := "".join(info_col.xpath('.//dt[text()="席数"]/following-sibling::dd[1]//text()').getall()):
            # only pattern "50席" -> 50
            # "フードコートの客席をご利用いただけます" (food-court seating) and "共有スペース" (shared space) are skipped
            if m := re.match(r"^\s*(\d+)\s*席", seats):
                item["extras"]["capacity:seats"] = m.group(1)

        if hours := "".join(
            info_col.xpath('.//dt[text()="営業時間"]/following-sibling::dd[1]/div[1]//text()').getall()
        ):
            item["opening_hours"] = self.parse_opening_hours(hours)

        service_icon_selector = './/ul[contains(@class, "icon")]/li'
        icon_image_selector = "./img/@src"
        for badge in info_col.xpath(service_icon_selector):
            icon_filename = badge.xpath(icon_image_selector).get().rsplit("/", 1)[-1]
            if icon_filename == "icon_pickup_detail.png":
                apply_yes_no(Extras.TAKEAWAY, item, True)
            elif icon_filename == "icon_delivery_detail.png":
                apply_yes_no(Extras.DELIVERY, item, True)
            elif icon_filename == "icon_eat-in_detail.png":
                apply_yes_no(Extras.INDOOR_SEATING, item, True)
            elif icon_filename == "icon_wifi_detail.png":
                apply_yes_no(Extras.WIFI, item, True)
                item["extras"]["internet_access:fee"] = "customers"
            elif icon_filename == "icon_soft_detail.svg":
                apply_yes_no(Extras.ICE_CREAM, item, True)
            # could server other drinks like tea, but assume only main drink coffee for safer side
            elif icon_filename == "icon_drink_detail.png":
                item["extras"]["drink:coffee"] = "served"
            elif icon_filename == "icon_drink02_detail.png":
                item["extras"]["drink:coffee"] = "served"
        # remaining ul.icon badges are menu/product claims with no OSM tag and are
        # intentionally dropped:
        # - あさオリグレ (morning promo: buy a drink 〜11:00, get a free Original Glazed)
        # - 出来立てドーナツ (freshly-made donuts)
        # - ブリュレ グレーズド (signature donut)
        # - 店舗限定 (store-limited availability)

        # third-party delivery providers from the 外部サービス (external services) block
        delivery_partner_selector = (
            './/dt[contains(text(), "外部サービス")]/following-sibling::dd[1]//p[contains(@class, "button")]/text()'
        )
        page_providers = [p.strip() for p in info_col.xpath(delivery_partner_selector).getall() if p.strip()]
        if page_providers:
            apply_yes_no(Extras.DELIVERY, item, True)
            item["extras"]["delivery:partner"] = ";".join(self.DELIVERY_PARTNERS.get(p, p) for p in page_providers)
            provider_qids = [q for q in (self.DELIVERY_PARTNERS_WIKIDATA.get(p) for p in page_providers) if q]
            if provider_qids:
                item["extras"]["delivery:partner:wikidata"] = ";".join(provider_qids)

        yield item

    def parse_opening_hours(self, text: str) -> str | None:
        # text is one line per <br>, each line has an optional day prefix:
        #   "10:00～21:00\n(土日祝)10:00～21:00\n※店内利用/ドリンクオーダーは20:00まで"
        #   line 1: every day       10:00-21:00
        #   line 2: Sat/Sun/holiday 10:00-21:00
        #   line 3: a note, skipped
        # A days value of None means "every day".
        # Holiday (祝) times are kept separately: the OpeningHours library only
        # knows Mo..Su, so public holidays must be appended to the string as PH.
        oh = OpeningHours()
        records: list[tuple[set[str] | None, str, str]] = []
        holiday_ranges: list[tuple[str, str]] = []
        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith("※") or line.startswith("（通常") or line.startswith("(通常"):
                continue
            if m := re.match(r"^\(([^)]*)\)\s*(.+)$", line):
                # "(土日祝) 10:00～21:00" -> days from the prefix, time from the rest
                days, holiday = self.parse_days(m.group(1))
                time_part = m.group(2)
            elif m := re.search(r"([^ 　]+?)のみ営業", line):
                # no day prefix; the days are stated inline,
                # e.g. "11:00～16:00 土日のみ営業" -> "土日" = Sat/Sun only
                days, holiday = self.parse_days(m.group(1))
                time_part = line
            else:
                # bare "10:00～21:00" -> every day
                days, holiday = None, False
                time_part = line
            if m := re.search(r"(\d{1,2}):(\d{2})\s*[〜～~\-ー]\s*(\d{1,2}):(\d{2})", time_part):
                open_time = f"{int(m.group(1)):02d}:{m.group(2)}"
                close_time = f"{int(m.group(3)):02d}:{m.group(4)}"
                if holiday:
                    holiday_ranges.append((open_time, close_time))
                records.append((days, open_time, close_time))

        # A bare "every day" line must not override a day that has its own
        # (usually shorter) line, so it only applies to days mentioned nowhere else.
        #   "10:00～21:00\n(日祝)10:00～20:00"
        #   -> Mo-Sa 10-21 (every-day minus {Su}), Su 10-20, PH 10-20
        specific_days = {day for days, _, _ in records if days is not None for day in days}
        for days, open_time, close_time in records:
            if days is None:
                days = set(DAYS) - specific_days
            for day in days:
                oh.add_range(day, open_time, close_time)

        result = oh.as_opening_hours()
        # e.g. "Mo-Sa 10:00-21:00; Su 10:00-20:00" -> "...; PH 10:00-20:00"
        if holiday_ranges and result:
            for open_time, close_time in holiday_ranges:
                result += f"; PH {open_time}-{close_time}"
            return result
        return result or None

    def parse_days(self, token: str) -> tuple[set[str], bool]:
        # turn a Japanese day group into OSM weekday abbreviations, e.g.
        #   "月～土"    -> {Mo, Tu, We, Th, Fr, Sa}
        #   "月～木・日祝" -> {Mo, Tu, We, Th, Su} with holiday=True
        #   "金・土"    -> {Fr, Sa}
        #   "祝" → public holiday
        holiday = "祝" in token
        days = set()
        for part in token.replace("祝", "祝・").split("・"):  # isolate 祝 onto its own segment
            part = part.strip()
            if not part or part == "祝":
                continue
            if "～" in part:
                # "月～土" -> day_range("Mo","Sa") = Mo, Tu, ..., Sa (inclusive)
                start, end = part.split("～", 1)
                days.update(day_range(DAYS_JP[start], DAYS_JP[end]))
            else:
                for day_char in part:
                    if day_char in DAYS_JP:
                        days.add(DAYS_JP[day_char])
        return days, holiday
