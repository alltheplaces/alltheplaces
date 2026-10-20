import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# The store finder list API only provides a store ID and coordinates. All
# other details (name, address, phone, opening hours) must be scraped from
# each store's own page.
HOURS_RE = re.compile(
    r"^(?P<open_h>\d{1,2})(?::(?P<open_m>\d{2}))?\s*(?:時)?\s*[~〜～\-]\s*"
    r"(?P<close_h>\d{1,2})(?::(?P<close_m>\d{2}))?\s*(?:時(?:(?P<close_m2>\d{1,2})分)?)?\s*$"
)

# Banners that are drugstore formatted, rather than general supermarket.
CHEMIST_BANNER_RE = re.compile(r"ドラッグ|トライウェル")
# A small format serving prepared food.
RESTAURANT_BANNER_RE = re.compile(r"グロッサリア")


class TrialJPSpider(Spider):
    name = "trial_jp"
    item_attributes = {"brand": "トライアル", "brand_wikidata": "Q11321723"}
    start_urls = ["https://www.trial-net.co.jp/wp-json/api/store"]

    async def start(self) -> AsyncIterator[Request]:
        yield JsonRequest(url=self.start_urls[0], callback=self.parse)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = Feature()
            item["ref"] = store["store_id"]
            item["lat"] = store["store_lat"]
            item["lon"] = store["store_lon"]
            item["website"] = f"https://www.trial-net.co.jp/shops/{item['ref']}/"

            yield Request(item["website"], callback=self.parse_store, cb_kwargs={"item": item})

    def parse_store(self, response: Response, item: Feature) -> Any:
        store_name = response.xpath('normalize-space(//strong[@class="store-name"]/text())').get()
        title = response.xpath('normalize-space(//meta[@property="og:title"]/@content)').get() or ""
        banner = title.split(" | ")[0].strip()
        if store_name and banner.endswith(store_name):
            banner = banner[: -len(store_name)].strip()

        item["branch"] = store_name or None

        if "タイヨー" in banner:
            item["brand"] = "タイヨー"
            item["brand_wikidata"] = None
        item["name"] = banner or store_name or item.get("brand")

        if CHEMIST_BANNER_RE.search(banner) or CHEMIST_BANNER_RE.search(store_name or ""):
            apply_category(Categories.SHOP_CHEMIST, item)
        elif RESTAURANT_BANNER_RE.search(banner) or RESTAURANT_BANNER_RE.search(store_name or ""):
            apply_category(Categories.RESTAURANT, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        postcode = response.xpath(
            'normalize-space(//td[strong[normalize-space(text())="住所"]]/following-sibling::td[1]/div[1])'
        ).get()
        if postcode:
            item["postcode"] = postcode.removeprefix("〒")

        addr_full = response.xpath(
            '//td[strong[normalize-space(text())="住所"]]/following-sibling::td[1]/text()[last()]'
        ).get()
        if addr_full:
            item["addr_full"] = addr_full.strip()

        item["phone"] = (
            response.xpath(
                'normalize-space(//td[strong[normalize-space(text())="電話番号"]]/following-sibling::td[1])'
            ).get()
            or None
        )

        self.parse_hours(item, response)

        yield item

    def parse_hours(self, item: Feature, response: Response) -> None:
        first_row = response.xpath(
            '(//td[strong[normalize-space(text())="営業時間"]]/following-sibling::td[1]'
            '//table[contains(@class,"store-info-table-inner")]/tr)[1]'
        )
        if not first_row:
            return

        # Use the number of actual <td> elements (not filtered text nodes) to tell
        # apart a single unlabelled cell (overall store hours, e.g. "24時間営業")
        # from a labelled row whose value happens to be blank or on another row.
        cells = [td.xpath("normalize-space(.)").get() for td in first_row.xpath("./td")]
        if len(cells) == 1:
            label, value = None, cells[0]
        elif len(cells) >= 2:
            label, value = cells[0], cells[1]
        else:
            return

        if label:
            # A labelled row means these are hours for a specific department or
            # service counter, not the store's overall opening hours, which are
            # not stated for this store.
            return

        if "24時間" in value:
            item["opening_hours"] = "24/7"
            return

        m = HOURS_RE.match(value)
        if not m:
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/unparsed")
            return

        open_h = int(m.group("open_h"))
        open_m = int(m.group("open_m") or 0)
        close_h = int(m.group("close_h"))
        close_m = int(m.group("close_m") or m.group("close_m2") or 0)
        if close_h >= 24:
            close_h -= 24

        oh = OpeningHours()
        oh.add_days_range(DAYS, f"{open_h:02d}:{open_m:02d}", f"{close_h:02d}:{close_m:02d}")
        item["opening_hours"] = oh
