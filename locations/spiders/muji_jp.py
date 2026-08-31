import json
import re
from typing import AsyncIterator, Iterable

from scrapy.http import Request, Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.geo import bbox_split
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Bounding box comfortably covering all of Japan, including Okinawa.
JAPAN_BBOX = ((46.0, 122.0), (20.0, 150.0))

# The searchBounds API silently truncates results to 100 per request, so
# any tile returning 100 results must be split further and re-queried.
RESULT_CAP = 100


class MujiJPSpider(CamoufoxSpider):
    name = "muji_jp"
    item_attributes = {"brand": "無印良品", "brand_wikidata": "Q708789"}
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawled_shop_cds: set[str] = set()

    async def start(self) -> AsyncIterator[Request]:
        for bbox in bbox_split(JAPAN_BBOX, lat_parts=4, lon_parts=4):
            yield self.make_request(bbox)

    def make_request(self, bbox: tuple[tuple[float, float], tuple[float, float]]) -> Request:
        (nw_lat, nw_lon), (se_lat, se_lon) = bbox
        url = (
            "https://www.muji.com/jp/ja/shop/api/searchBounds"
            f"?swLat={se_lat}&swLng={nw_lon}&neLat={nw_lat}&neLng={se_lon}&lang=ja"
        )
        return Request(url, callback=self.parse, cb_kwargs={"bbox": bbox})

    def parse(
        self, response: Response, bbox: tuple[tuple[float, float], tuple[float, float]]
    ) -> Iterable[Feature | Request]:
        try:
            stores = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning("Failed to decode JSON for bbox %s", bbox)
            return

        if len(stores) >= RESULT_CAP:
            for sub_bbox in bbox_split(bbox, lat_parts=2, lon_parts=2):
                yield self.make_request(sub_bbox)
            return

        for store in stores:
            yield from self.parse_store(store)

    def parse_store(self, store: dict) -> Iterable[Feature]:
        shop_cd = store.get("shop_cd")
        if not shop_cd or shop_cd in self.crawled_shop_cds:
            return
        self.crawled_shop_cds.add(shop_cd)

        item = Feature()
        item["ref"] = shop_cd
        item["name"] = store.get("shopname")
        item["addr_full"] = store.get("shopaddress")
        item["country"] = "JP"
        item["lat"] = store.get("latitude")
        item["lon"] = store.get("longitude")
        item["phone"] = store.get("tel")
        item["website"] = f"https://www.muji.com/jp/ja/shop/detail/{shop_cd}"

        if zipcode := store.get("zipcode"):
            zipcode = re.sub(r"\D", "", zipcode)
            if len(zipcode) == 7:
                item["postcode"] = f"{zipcode[:3]}-{zipcode[3:]}"

        if hours := self.parse_hours(store.get("weekday_business_time")):
            item["opening_hours"] = hours

        apply_category(Categories.SHOP_VARIETY_STORE, item)

        yield item

    @staticmethod
    def parse_hours(raw: str | None) -> OpeningHours | None:
        if not raw:
            return None
        m = re.match(r"^(\d{1,2}:\d{2})[~～](\d{1,2}:\d{2})$", raw.strip())
        if not m:
            return None
        oh = OpeningHours()
        for day in DAYS:
            oh.add_range(day, m.group(1), m.group(2))
        return oh
