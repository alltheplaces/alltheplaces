import re
from datetime import date
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class VapostoreFRSpider(Spider):
    name = "vapostore_fr"
    item_attributes = {"brand": "Vapostore", "brand_wikidata": "Q91257968", "name": "Vapostore"}
    allowed_domains = ["www.vapostore.com"]
    start_urls = ["https://www.vapostore.com/magasins-cigarette-electronique"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        websites = {
            url.rsplit("-", 1)[1]: url
            for url in response.xpath('//a[contains(@href, "/boutiques/")]/@href').getall()
            if re.search(r"/boutiques/[^/]+/.+-\d+$", url)
        }
        script = response.xpath('//script[contains(text(), "var vapomagasins")]/text()').get()
        stores = chompjs.parse_js_object(script.split("var vapomagasins =", 1)[1])["magasins"]
        today = date.today().isoformat()

        for store in stores.values():
            if store["is_active"] != "1" or store["open_soon"] != "0" or store["permanent_closure"] != "0":
                continue
            if store["start_temporary_closure"] <= today <= store["end_temporary_closure"]:
                continue

            item = Feature()
            item["ref"] = store["id_vapo_magasin"]
            item["branch"] = re.sub(
                r"^VAPOSTORE\s*-?\s*(.+?)(?:\s*-?\s*Magasin de cigarette.*)?$", r"\1", store["title"].strip()
            )
            item["street_address"] = store["address"]
            item["postcode"] = store["zip"].strip()
            item["city"] = store["city"].strip()
            item["country"] = OVERSEAS_COUNTRIES.get(item["postcode"][:3], "FR")
            item["phone"] = store["phone"]
            item["lat"] = store["g_lat"]
            item["lon"] = store["g_long"]
            item["website"] = websites.get(item["ref"])
            item["opening_hours"] = self.parse_hours(store)
            # NSI only covers mainland France, not the Guadeloupe stores
            apply_category(Categories.SHOP_E_CIGARETTE, item)
            yield item

    @staticmethod
    def parse_hours(store: dict) -> OpeningHours | None:
        days = {day: store["h_{}".format(day.lower())].strip() for day in DAYS_FULL}
        # Notes such as "Exceptionnellement fermé le 1er août" replace the usual hours
        if not all(days.values()) or any("exception" in hours.lower() for hours in days.values()):
            return None
        oh = OpeningHours()
        for day, hours in days.items():
            times = re.findall(r"(\d{1,2})\s*[hH:]\s*(\d{2})?", hours)
            if "ferm" in hours.lower() and not times:
                oh.set_closed(day)
                continue
            if not times or len(times) % 2:
                return None
            times = ["{:0>2}:{}".format(h, m or "00") for h, m in times]
            for open_time, close_time in zip(times[::2], times[1::2]):
                oh.add_range(day, open_time, close_time)
        return oh
