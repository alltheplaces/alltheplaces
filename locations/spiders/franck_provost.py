import json
import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class FranckProvostSpider(SitemapSpider):
    name = "franck_provost"
    item_attributes = {"brand": "Franck Provost", "brand_wikidata": "Q62805922"}
    sitemap_urls = ["https://www.franckprovost.com/sitemaps/sitemap-hairdressers.xml"]
    sitemap_rules = [(r"/salons/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The salon object is embedded (quote-escaped) inside a Next.js RSC flight chunk.
        payload = "".join(
            json.loads(chunk)
            for chunk in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', response.text)
        )
        if (start := payload.find('"hairdresser":{')) < 0:
            return
        salon = json.JSONDecoder().raw_decode(payload, start + len('"hairdresser":'))[0]

        common = salon.get("common") or {}

        item = Feature()
        item["ref"] = salon.get("code") or str(salon.get("id"))
        item["name"] = "Franck Provost"
        item["branch"] = common.get("brand") or ""
        item["addr_full"] = ", ".join(filter(None, [common.get("addressLine2"), common.get("addressLine1")]))
        item["city"] = salon.get("city")
        item["phone"] = common.get("tel")
        item["email"] = (salon.get("infos") or {}).get("email")
        item["website"] = response.url

        if geo := (salon.get("pictureAndMap") or {}).get("map"):
            item["lat"] = geo.get("latitude")
            item["lon"] = geo.get("longitude")

        item["opening_hours"] = OpeningHours()
        for day in (salon.get("toBeComputed") or {}).get("openUntil", {}).get("hours") or []:
            if day.get("closed") or not (day.get("opening") and day.get("closing")):
                continue
            item["opening_hours"].add_range(DAYS[day["day"] - 1], day["opening"], day["closing"])

        apply_category(Categories.SHOP_HAIRDRESSER, item)

        yield item
