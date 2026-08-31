import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_CHARS = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")

HOURS_RE = re.compile(r"(午前|午後)(\d{1,2})時(?:(\d{1,2})分)?[~〜～-](午前|午後)(\d{1,2})時(?:(\d{1,2})分)?")


class DocomoShopJPSpider(SitemapSpider):
    name = "docomo_shop_jp"
    item_attributes = {"brand": "NTT docomo", "brand_wikidata": "Q853958"}
    sitemap_urls = ["https://shop.smt.docomo.ne.jp/sitemap.xml"]
    # The sitemap also lists info/service pages and secondary per-shop pages
    # (e.g. "0300304163300/02.html"); only the shop's primary page is wanted.
    sitemap_rules = [(r"/shop_detail/\d+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        body = response.css("body")
        shop_name = body.attrib.get("data-shopname")
        if not shop_name:
            # A handful of sitemap entries 404 (stale listing for a closed shop).
            return

        ref_match = re.search(r"/shop_detail/(\d+)/", response.url)
        if not ref_match:
            return

        item = Feature()
        item["ref"] = ref_match.group(1)
        item["name"] = shop_name
        item["branch"] = shop_name.removeprefix("ドコモショップ").strip()
        item["website"] = response.url
        item["country"] = "JP"
        item["lat"] = body.attrib.get("data-lat")
        item["lon"] = body.attrib.get("data-lng")

        hours_text = None
        holiday_text = None

        for column in response.css(".store-basic-information-0002-column"):
            title = column.css(".store-basic-information-0002-title::text").get("").strip()
            if title == "住所":
                self._parse_address(item, column)
            elif title == "営業時間":
                hours_text = " ".join(
                    t.strip() for t in column.css(".store-basic-information-0002__text-area ::text").getall()
                )
            elif title == "定休日":
                holiday_text = " ".join(
                    t.strip() for t in column.css(".store-basic-information-0002__text-area ::text").getall()
                )

        if hours_text and (oh := self._parse_hours(hours_text, holiday_text)):
            item["opening_hours"] = oh

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        yield item

    @staticmethod
    def _parse_address(item: Feature, column) -> None:
        addr_html = column.css("p.store-basic-information-0002_margin.sm-txt").get()
        if not addr_html:
            return
        lines = [re.sub(r"<[^>]+>", "", part).strip() for part in re.split(r"<br\s*/?>", addr_html)]
        lines = [line for line in lines if line]
        if lines:
            item["addr_full"] = " ".join(lines)

        # The first tel: link is a shared regional free-dial (0120) number
        # reused across multiple shops; the second is the shop's own direct
        # line, which is what's wanted here.
        tel_hrefs = column.css("a[href^='tel:']::attr(href)").getall()
        local_numbers = [h.removeprefix("tel:") for h in tel_hrefs if not h.removeprefix("tel:").startswith("0120")]
        if local_numbers:
            item["phone"] = local_numbers[-1]
        elif tel_hrefs:
            item["phone"] = tel_hrefs[-1].removeprefix("tel:")

    @staticmethod
    def _to_24h(marker: str, hour: str, minute: str | None) -> str:
        h = int(hour)
        m = int(minute) if minute else 0
        if marker == "午後" and h != 12:
            h += 12
        if marker == "午前" and h == 12:
            h = 0
        return f"{h:02d}:{m:02d}"

    def _parse_hours(self, hours_text: str, holiday_text: str | None) -> OpeningHours | None:
        matches = list(HOURS_RE.finditer(hours_text))
        if not matches:
            return None

        open_time = self._to_24h(matches[0].group(1), matches[0].group(2), matches[0].group(3))
        close_time = self._to_24h(matches[0].group(4), matches[0].group(5), matches[0].group(6))

        oh = OpeningHours()

        # A second time range usually describes a narrower internal "受付時間"
        # (reception/sign-up desk cut-off) rather than the shop's own hours,
        # and is intentionally ignored - except when the text between the two
        # ranges explicitly says weekends have their own hours, which is a
        # genuine difference in when the shop itself opens/closes.
        if (
            len(matches) > 1
            and "毎週土曜" in hours_text[matches[0].end() : matches[1].start()]
            and "毎週日曜" in hours_text[matches[0].end() : matches[1].start()]
        ):
            weekend_open = self._to_24h(matches[1].group(1), matches[1].group(2), matches[1].group(3))
            weekend_close = self._to_24h(matches[1].group(4), matches[1].group(5), matches[1].group(6))
            oh.add_days_range(["Mo", "Tu", "We", "Th", "Fr"], open_time, close_time)
            oh.add_days_range(["Sa", "Su"], weekend_open, weekend_close)
        else:
            oh.add_days_range(DAYS, open_time, close_time)

        # "定休日" (regular closing day) is usually either "無休" (no closure)
        # or a specific weekday closed every week ("毎週火曜"). A third form,
        # closure on the Nth occurrence of a weekday each month (e.g.
        # "第２木曜"), can't be expressed by the weekly-only OpeningHours
        # helper here, so it's deliberately left unencoded rather than
        # mis-stated as a full weekly closure.
        if holiday_text:
            normalised = holiday_text.translate(FULLWIDTH_DIGITS)
            if normalised.startswith("毎週"):
                if day_match := re.search(r"([月火水木金土日])曜", normalised):
                    oh.set_closed(DAY_CHARS[day_match.group(1)])

        return oh
