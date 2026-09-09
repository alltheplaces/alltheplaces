import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr"]


class BankOfYokohamaJPSpider(CrawlSpider):
    name = "bank_of_yokohama_jp"
    item_attributes = {"brand": "横浜銀行", "brand_wikidata": "Q2744340", "name": "横浜銀行"}
    allowed_domains = ["sasp.mapion.co.jp"]
    start_urls = ["https://sasp.mapion.co.jp/b/boy/attr/?t=attr_con&x=63&y=18"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/b/boy/attr/\?start=\d+", restrict_xpaths='//a[@id="m_nextpage_link"]'),
            follow=True,
        ),
        Rule(LinkExtractor(allow=r"/b/boy/info/\d+/$"), callback="parse_store"),
    ]

    def parse_store(self, response: Response) -> Iterable[Feature]:
        if not (m := re.search(r"window\.infoJSON\s*=\s*(\{.*?\});", response.text)):
            return
        # The site's own escaping is invalid JSON for some stores, e.g. a
        # literal "\'" inside "remarks" (valid in a JS string, not in JSON).
        raw = re.sub(r'\\(?!["\\/bfnrtu])', "", m.group(1))
        data = json.loads(raw)

        item = Feature()
        item["ref"] = data.get("id")
        item["branch"] = data.get("name")
        item["addr_full"] = data.get("full_address")
        item["postcode"] = data.get("zip_code")
        item["website"] = response.url

        if kencode := data.get("kencode"):
            item["state"] = "JP-" + kencode

        if tel := data.get("tel"):
            item["phone"] = tel

        # window.infoJSON's plain latitude/longitude are correct WGS84 and
        # match real branch addresses closely; the page's separate
        # schema.org/GeoCoordinates "geo" microdata applies a spurious datum
        # correction landing ~300-400m away, the same platform quirk already
        # confirmed for this Mapion storefinder in mister_donut_jp.py.
        item["lat"] = data.get("latitude")
        item["lon"] = data.get("longitude")

        oh = OpeningHours()
        if data.get("kind") == "ATMコーナー":
            # A standalone ATM corner, not a staffed branch: use the ATM's
            # own hours, which can differ between weekdays and weekends.
            self.add_hours(oh, WEEKDAYS, data.get("atm_time"))
            self.add_hours(oh, ["Sa"], data.get("atm_sat"))
            self.add_hours(oh, ["Su"], data.get("atm_sun"))
            apply_category(Categories.ATM, item)
        else:
            # "handle_time" is the teller counter's opening hours, e.g.
            # "9:00～11:30<br/>12:30～15:00" for branches with a lunch
            # closure. Transfer-only branches have no counter and so no
            # handle_time, leaving opening_hours blank.
            self.add_hours(oh, WEEKDAYS, data.get("handle_time"))
            apply_category(Categories.BANK, item)
        if oh:
            item["opening_hours"] = oh

        yield item

    @staticmethod
    def add_hours(oh: OpeningHours, days: list[str], time_range: str | None):
        if not time_range:
            return
        for segment in re.split(r"<br\s*/?>", time_range):
            if hours := re.match(r"(\d{1,2}):(\d{2})[~〜～](\d{1,2}):(\d{2})", segment.strip()):
                # Some ATMs use "25:00" style times to mean 01:00 the next
                # day; normalise so OpeningHours' own overnight handling
                # (triggered when close < open) picks it up.
                open_time = f"{int(hours.group(1)) % 24:02d}:{hours.group(2)}"
                close_time = f"{int(hours.group(3)) % 24:02d}:{hours.group(4)}"
                oh.add_days_range(days, open_time, close_time)
