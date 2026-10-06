import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class MongolPostMNSpider(Spider):
    name = "mongol_post_mn"
    item_attributes = {"operator": "Mongol Post", "operator_wikidata": "Q4301626"}
    allowed_domains = ["www.mongolpost.mn"]
    # A Next.js page; the branch list is embedded in the server components payload as "storeLocations".
    start_urls = ["https://www.mongolpost.mn/mn/post-offices"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        chunks = re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', response.text)
        data = "".join(json.loads(chunk) for chunk in chunks)
        start = data.find('"storeLocations":[')
        locations = json.JSONDecoder().raw_decode(data, start + len('"storeLocations":'))[0]
        seen = set()
        for location in locations:
            title = (location.get("title") or "").strip()
            # Most entries are EasyBox parcel lockers.
            if "easybox" in title.lower():
                continue
            # The same branch is sometimes listed twice under different ids.
            if (title, location.get("map")) in seen:
                continue
            seen.add((title, location.get("map")))
            lat, _, lon = (location.get("map") or "").partition(",")
            # A few province offices only have whole-degree placeholder coordinates ("49,100").
            if not lat or not lon or ("." not in lat and "." not in lon):
                self.crawler.stats.inc_value("atp/mongol_post_mn/placeholder_coordinates")
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["name"] = title
            item["lat"], item["lon"] = lat.strip(), lon.strip()
            item["addr_full"] = re.sub(r"\s+", " ", location.get("address") or "").strip(" ,")
            phones = [p.strip() for p in (location.get("phone") or "").split(",")]
            item["phone"] = "; ".join(p for p in phones if p and p != "12345678")
            item["image"] = location.get("photo")
            item["country"] = "MN"
            if location.get("code"):
                item["extras"]["ref:mongol_post"] = location["code"]
            item["opening_hours"] = self.parse_hours(location.get("timeSheets") or [])
            apply_category(Categories.POST_OFFICE, item)
            yield item

    @staticmethod
    def parse_hours(time_sheets: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for row in time_sheets:
            day = DAYS[row["dow"]]  # 0 = Monday
            if row.get("day_off"):
                oh.set_closed(day)
            elif row.get("open_at") and row.get("close_at"):
                oh.add_range(day, row["open_at"], row["close_at"])
        return oh
