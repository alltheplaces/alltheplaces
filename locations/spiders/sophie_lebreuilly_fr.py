import re
from typing import Any, Iterable
from urllib.parse import unquote_plus

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class SophieLebreuillyFRSpider(Spider):
    name = "sophie_lebreuilly_fr"
    item_attributes = {"brand": "Sophie Lebreuilly", "brand_wikidata": "Q66372229"}
    start_urls = ["https://sophie-lebreuilly.com/nos-boulangeries-sophie/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for iframe in response.xpath('//iframe[contains(@src, "adelyashop.com")]/@src').getall():
            yield response.follow(iframe, callback=self.parse_locator)

    def parse_locator(self, response: Response, **kwargs: Any) -> Any:
        for ref in response.xpath("//div[@data-codegroup]/@data-codegroup").getall():
            yield Request(
                f"https://www.adelyashop.com/Adelyaview/sophielebreuilly/store/Boulangerie-Sophie.html?sl_cg={ref}",
                callback=self.parse_store,
                cb_kwargs={"ref": ref},
            )

        if next_page := response.xpath('//a[i[contains(@class, "fa-forward")]]/@href').get():
            yield response.follow(next_page, callback=self.parse_locator)

    def parse_store(self, response: Response, ref: str) -> Iterable[Feature]:
        item = Feature(ref=ref, website=response.url, country="FR")

        if name := response.xpath('//div[@id="address"]/h2/text()').get():
            item["branch"] = re.sub(r"(?i)^boulangerie\s+(?:sophie\s+)?(?:lebreuilly\s+)?[-–—]?\s*", "", name).strip()

        lat = response.xpath('//div[@id="map-container"]/@data-lat').get()
        lon = response.xpath('//div[@id="map-container"]/@data-lng').get()
        if lat and lon and (float(lat), float(lon)) != (0.0, 0.0):
            item["lat"], item["lon"] = lat, lon

        item["phone"] = response.xpath('//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

        if daddr := response.xpath('//a[@id="itinerary"]/@href').re_first(r"daddr=([^&]+)"):
            lines = [line.strip() for line in unquote_plus(daddr).splitlines() if line.strip()]
            if lines and lines[-1].upper() == "FR":
                lines.pop()
            if lines and (m := re.match(r"^(\d{5})\s+(.+)$", lines[-1])):
                item["postcode"], item["city"] = m.groups()
                lines.pop()
            if lines:
                item["street_address"] = ", ".join(lines)

        if raw_hours := response.xpath('//p[contains(@class, "opening-hours")]//span/text()').get():
            item["opening_hours"] = self.parse_opening_hours(raw_hours)

        apply_category(Categories.SHOP_BAKERY, item)

        yield item

    def parse_opening_hours(self, text: str) -> OpeningHours:
        oh = OpeningHours()
        day_p = r"lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
        for clause in re.split(rf",|;|\bet\b(?=\s*(?:du\s+|le\s+|au\s+)?(?:{day_p})\b)", (text or "").lower()):
            days = []
            if m := re.search(rf"({day_p})\s+au\s+({day_p})", clause):
                days = day_range(sanitise_day(m[1], DAYS_FR), sanitise_day(m[2], DAYS_FR))
            elif m := re.search(rf"({day_p})", clause):
                days = [sanitise_day(m[1], DAYS_FR)]

            for t1, t2 in re.findall(r"(\d{1,2}h\d*)\s*à\s*(\d{1,2}h\d*)", clause):
                oh.add_days_range(days, t1, t2, time_format=["%Hh%M", "%Hh"])

        return oh
