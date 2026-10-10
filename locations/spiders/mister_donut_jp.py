import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.storefinders.mapion import MapionSpider


class MisterDonutJPSpider(MapionSpider):
    name = "mister_donut_jp"
    item_attributes = {"brand": "ミスタードーナツ", "brand_wikidata": "Q1065819"}
    allowed_domains = ["md.mapion.co.jp"]
    feature_url_template = "https://md.mapion.co.jp/b/misterdonut/attr/?t=attr_con&start={}"

    def post_process_item(self, item: Feature, data: dict, response: Response) -> Iterable[Feature]:
        item["name"] = None
        item["branch"] = data.get("map_name")

        if (open_time := data.get("open_time")) and (close_time := data.get("close_time")):
            # close_time occasionally has a trailing free-text exception note
            # (e.g. "23:00<br>Fri/Sat open until 0:30") tacked on; keep just
            # the base daily hours which the site displays as the headline
            # opening hours for the store.
            if close_match := re.match(r"\d{1,2}:\d{2}", close_time):
                oh = OpeningHours()
                oh.add_days_range(DAYS, open_time, close_match.group())
                item["opening_hours"] = oh

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "donut"

        yield item
