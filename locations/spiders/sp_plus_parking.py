import re
from typing import Any, Iterable, Optional

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class SpPlusParkingSpider(SitemapSpider):
    name = "sp_plus_parking"
    item_attributes = {"brand": "SP+", "brand_wikidata": "Q7598289"}
    sitemap_urls = ["https://parking.com/sitemap.xml"]
    sitemap_rules = [(r"/lot/[^/]+$", "parse_lot_page")]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse_lot_page(self, response: Response) -> Iterable[Request]:
        yield Request(
            response.url.rstrip("/") + ".json",
            callback=self.parse_lot_json,
            cb_kwargs={"page_url": response.url},
        )

    def parse_lot_json(self, response: Response, page_url: str = "", **kwargs: Any) -> Iterable[Feature]:
        data = response.json()
        lot = data.get("lot") or data
        item = DictParser.parse(lot)
        item["website"] = page_url
        item["street_address"] = item.pop("addr_full", None)

        name = (item.pop("name") or "").strip()
        if name.startswith("(") and ") " in name:
            item["branch"] = name.split(") ", 1)[1].strip()
        else:
            item["branch"] = name

        if addr2 := lot.get("addressLine2"):
            parts = addr2.rsplit(",", 1)
            item["city"] = parts[0].strip() if len(addr2.rsplit(",", 1)) == 2 else addr2
            if len(parts) == 2:
                sp = parts[1].strip().split()
                item["state"] = sp[0] if sp else None
                item["postcode"] = sp[1] if len(sp) > 1 else None

        features = lot.get("features") or {}
        raw_hours = features.get("hoursOfOperation")

        if parsed_hours := self.parse_opening_hours(raw_hours):
            item["opening_hours"] = parsed_hours

        apply_category(Categories.PARKING, item)
        apply_yes_no(Fuel.ELECTRIC, item, (lot.get("features") or {}).get("electricVehicleCharging", False))

        yield item

    def parse_opening_hours(self, hours_string: Optional[str]) -> OpeningHours | str | None:
        if not hours_string:
            return None

        hours_string = hours_string.strip()
        if "24 / 7" in hours_string or "24/7" in hours_string:
            return "24/7"

        oh = OpeningHours()
        oh.add_ranges_from_string(re.sub(r"(?i)\bopen\b", "", re.sub(r"(?i)24\s*hours?", "00:00-23:59", hours_string)))

        return oh or None
