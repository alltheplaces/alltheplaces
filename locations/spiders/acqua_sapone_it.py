from typing import Any
from urllib.parse import unquote

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import _get_possible_links
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import Feature


class AcquaSaponeITSpider(SitemapSpider):
    name = "acqua_sapone_it"
    item_attributes = {"brand": "Acqua & Sapone", "brand_wikidata": "Q51079044"}
    sitemap_urls = ["https://www.acquaesapone.it/puntovendita-sitemap.xml"]
    sitemap_rules = [(r"/puntivendita/.+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url
        item["website"] = response.url

        for link in _get_possible_links(response):
            if "/place/" in link:
                item["addr_full"] = unquote(link.split("/place/")[-1].replace("+", " "))
                break

        item["phone"] = response.xpath('//a[starts-with(@href,"tel:")]/@href').get("").removeprefix("tel:")

        self._parse_hours(item, response)

        apply_category(Categories.SHOP_CHEMIST, item)

        yield item

    def _parse_hours(self, item: Feature, response: Response) -> None:
        hours_texts = response.xpath('//*[contains(text(),"LUNED")]/ancestor::section[1]//p/text()').getall()
        if not hours_texts:
            return

        days = []
        times = []
        for text in hours_texts:
            text = text.strip()
            if not text:
                continue
            if sanitise_day(text, DAYS_IT):
                days.append(text)
            else:
                times.append(text)

        if len(days) != len(times):
            return

        oh = OpeningHours()
        for day_name, time_range in zip(days, times):
            day = sanitise_day(day_name, DAYS_IT)
            try:
                for period in time_range.split(","):
                    period = period.strip()
                    if "-" in period:
                        open_time, close_time = period.split("-", 1)
                        oh.add_range(day, open_time.strip(), close_time.strip())
            except Exception:
                continue
        item["opening_hours"] = oh
