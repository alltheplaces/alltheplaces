import json
import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Detail pages embed a JS call like:
#   mapsinitialize([{...nearby parkings incl. this one...}], <lat>, <lon>, <id>, <zoom>);
# The array holds every parking shown on the page's map (this one plus
# nearby ones sharing a station), so the current parking is picked out by
# matching the id passed as the third trailing argument.
MAPSINITIALIZE_CALL = re.compile(r"mapsinitialize\(")
MAPSINITIALIZE_TAIL = re.compile(r",([\d.]+),([\d.]+),(\d+),(\d+)\)")

# A national toll-free ("0120") support line repeated across roughly half of
# all locations, so it does not identify any particular branch.
GENERIC_PHONE_PREFIX = "0120"


class CycaParkingJPSpider(SitemapSpider):
    name = "cyca_parking_jp"
    item_attributes = {"brand": "サイカパーキング", "brand_wikidata": "Q127958401"}
    allowed_domains = ["charinavi72.jp"]
    sitemap_urls = ["https://www.charinavi72.jp/sitemap.xml"]
    sitemap_rules = [(r"/system/Parkings/detail/\d+$", "parse")]

    def parse(self, response: Response):
        call = MAPSINITIALIZE_CALL.search(response.text)
        if not call:
            # Delisted parkings redirect away from their old detail URL.
            return

        try:
            data, idx = json.JSONDecoder().raw_decode(response.text, call.end())
        except ValueError:
            return

        tail = MAPSINITIALIZE_TAIL.match(response.text, idx)
        if not tail:
            return

        current_id = int(tail.group(3))
        entry = next((e for e in data if e.get("Parkings", {}).get("id") == current_id), None)
        if not entry:
            return

        parking = entry["Parkings"]
        area = entry.get("Areas") or {}

        phone = parking.get("tel") or None
        if phone and phone.startswith(GENERIC_PHONE_PREFIX):
            phone = None

        oh = None
        hours = (parking.get("business_hours") or "").strip()
        if "24時間" in hours or "２４時間" in hours:
            oh = OpeningHours()
            for day in DAYS:
                oh.add_range(day, "00:00", "24:00")

        item = Feature()
        item["ref"] = str(parking["id"])
        item["name"] = parking.get("name")
        item["lat"] = parking.get("latitude")
        item["lon"] = parking.get("longitude")
        item["street_address"] = "".join(
            filter(None, [area.get("prefecture"), area.get("city"), parking.get("address")])
        )
        item["country"] = "JP"
        item["phone"] = phone
        item["website"] = response.url
        if oh:
            item["opening_hours"] = oh

        apply_category(Categories.BICYCLE_PARKING, item)
        yield item

        has_motorcycle = (
            bool(parking.get("charge_mc"))
            or bool(parking.get("contract_mc_time"))
            or bool(parking.get("contract_mc_month"))
        )
        if has_motorcycle:
            motorcycle_item = item.deepcopy()
            motorcycle_item["ref"] = f"{parking['id']}_motorcycle"
            apply_category(Categories.MOTORCYCLE_PARKING, motorcycle_item)
            yield motorcycle_item
