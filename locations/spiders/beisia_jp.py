import re
import unicodedata
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider

TIME_RANGE = r"(\d{1,2}:\d{2})[~〜-](\d{1,2}:\d{2})"


class BeisiaJPSpider(GogaStoreLocatorSpider):
    name = "beisia_jp"

    start_urls = ["https://map.beisia.co.jp/api/points"]
    item_attributes = {
        "brand": "ベイシア",
        "brand_wikidata": "Q11336776",
    }
    website_formatter = "https://map.beisia.co.jp/map/{}"

    SINGLE = re.compile(rf"^{TIME_RANGE}$")
    WEEKDAY_WEEKEND = re.compile(rf"^平日{TIME_RANGE}\n土日{TIME_RANGE}$")
    ONE_DAY_DIFFERENT = re.compile(rf"^{TIME_RANGE}\((\w曜日)のみ{TIME_RANGE}\)$")

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = "ベイシア"
        item["branch"] = source_feature.get("name")
        # "ふりがな" is the reading of the address (e.g. "アイチケンガマゴオリシ..."),
        # not of the store name, so it is not used for branch:ja-Hira.
        item["opening_hours"] = self.parse_opening_hours(source_feature.get("営業時間"))
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item

    def parse_opening_hours(self, value: str | None) -> OpeningHours | None:
        """Read the common formats; anything with notes, floors or announcements gives no hours."""
        lines = [re.sub(r"\s+", "", line) for line in unicodedata.normalize("NFKC", value or "").strip().splitlines()]
        text = "\n".join(lines)
        oh = OpeningHours()
        if match := self.SINGLE.match(text):
            oh.add_days_range(DAYS, match.group(1), match.group(2))
        elif match := self.WEEKDAY_WEEKEND.match(text):
            oh.add_days_range(DAYS_WEEKDAY, match.group(1), match.group(2))
            oh.add_days_range(DAYS_WEEKEND, match.group(3), match.group(4))
        elif (match := self.ONE_DAY_DIFFERENT.match(text)) and (day := DAYS_JP.get(match.group(3))):
            oh.add_days_range([d for d in DAYS if d != day], match.group(1), match.group(2))
            oh.add_range(day, match.group(4), match.group(5))
        else:
            return None
        return oh
