import json
import re
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# The store list is served from a single wide "tile" (x=63&y=18) which
# encompasses the whole of Japan, rather than needing to be paginated
# through many individual map tiles like some other Mapion based sites.
LIST_URL = "https://md.mapion.co.jp/b/misterdonut/attr/?t=attr_con&x=63&y=18&start={}"


class MisterDonutJPSpider(Spider):
    name = "mister_donut_jp"
    item_attributes = {"brand": "ミスタードーナツ", "brand_wikidata": "Q1065819"}
    allowed_domains = ["md.mapion.co.jp"]
    start_urls = [LIST_URL.format(1)]

    def parse(self, response: Response) -> Iterable[Request]:
        if m := re.search(r'pager-num">\d+/(\d+)', response.text):
            if response.url == self.start_urls[0]:
                for page in range(2, int(m.group(1)) + 1):
                    yield Request(LIST_URL.format(page), callback=self.parse)

        for href in response.xpath('//li[@class="list-item"]//a[h2]/@href').getall():
            yield response.follow(href, callback=self.parse_store)

    def parse_store(self, response: Response) -> Iterable[Feature]:
        m = re.search(r"window\.infoJSON\s*=\s*(\{.*?\});", response.text)
        if not m:
            return
        data = json.loads(m.group(1))

        item = Feature()
        item["ref"] = data.get("id")
        item["name"] = self.item_attributes["brand"]
        item["branch"] = data.get("map_name")
        item["addr_full"] = data.get("full_address")
        item["postcode"] = data.get("zip_code")
        item["website"] = response.url

        if tel := data.get("tel"):
            item["phone"] = "+81 " + tel

        # Despite the "Tky" suffix the site applies to these fields in its
        # schema.org markup (latitudeTky/longitudeTky), window.infoJSON's
        # plain latitude/longitude values are already correct WGS84 and
        # match real store addresses/landmarks closely. The page's
        # schema.org/GeoCoordinates microdata is the one that's wrong: it
        # applies a spurious Tokyo Datum correction to already-WGS84 data,
        # landing stores ~300-400m away (verified against several stores'
        # real-world addresses), so it must not be used.
        item["lat"] = data.get("latitude")
        item["lon"] = data.get("longitude")

        if (open_time := data.get("open_time")) and (close_time := data.get("close_time")):
            # close_time occasionally has a trailing free-text exception note
            # (e.g. "23:00<br>Fri/Sat open until 0:30") tacked on; keep just
            # the base daily hours which the site displays as the headline
            # opening hours for the store.
            if close_match := re.match(r"\d{1,2}:\d{2}", close_time):
                oh = OpeningHours()
                oh.add_days_range(DAYS, open_time, close_match.group())
                item["opening_hours"] = oh.as_opening_hours()

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "donut"

        yield item
