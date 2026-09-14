import json
import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature


class OTacosSpider(SitemapSpider):
    name = "o_tacos"
    item_attributes = {"brand": "O'Tacos", "brand_wikidata": "Q28494040"}
    sitemap_urls = ["https://restaurants.o-tacos.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.o-tacos\.com(?:/[^/]+){5}$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        payload = "".join(
            json.loads(chunk)
            for chunk in re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', response.text)
        )
        if (start := payload.find('"place":{"id":"loc_')) < 0:
            return
        place = json.JSONDecoder().raw_decode(payload, start + len('"place":'))[0]
        place.update(place.pop("address"))
        place["phone"] = (place.pop("contact", None) or {}).get("mainPhone")

        item = DictParser.parse(place)
        item.pop("name", None)
        item["branch"] = place.get("shortName")
        item["street_address"] = place.get("line1")
        item["website"] = response.url

        item["opening_hours"] = OpeningHours()
        for day in (place.get("openings") or {}).get("businessOpenings") or []:
            for timetable in day["timetables"]:
                item["opening_hours"].add_range(
                    DAYS_FROM_SUNDAY[day["dayOfWeek"] - 1], timetable["open"], timetable["close"]
                )

        apply_category(Categories.FAST_FOOD, item)
        yield item
