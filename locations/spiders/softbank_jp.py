from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature

# The API clamps its radius to about 38 km whatever `dist` asks for, so cells wider than that
# leave gaps: 48 km centroids return 966 shops against 2157 from the 24 km set.
SEARCH_RADIUS_KM = 24


class SoftbankJPSpider(Spider):
    name = "softbank_jp"
    item_attributes = {"brand": "SoftBank", "brand_wikidata": "Q2214105"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        for latitude, longitude in country_iseadgg_centroids(["JP"], SEARCH_RADIUS_KM):
            yield JsonRequest(
                url="https://www.softbank.jp/shop/d/system/v1/api/shop-search/"
                f"?type=current&sort=0&results=10000&lat={latitude}&lon={longitude}&dist=50"
            )

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Cells overlap, so the same shop arrives from several centroids. The pipeline
        # deduplicates on ref.
        for shop in response.json().get("item") or []:
            yield self.parse_shop(shop)

    def parse_shop(self, shop: dict) -> Feature:
        item = Feature()

        item["ref"] = shop["shop_id"]
        item["website"] = f"https://www.softbank.jp/shop/search/detail/{item['ref']}/"
        item["branch"] = (shop.get("shop_name") or {}).get("name")

        item["country"] = "JP"
        item["addr_full"] = shop.get("address")
        item["phone"] = shop.get("tel")

        geo = shop.get("geo") or {}
        item["lat"] = geo.get("lat")
        item["lon"] = geo.get("lon")

        item["opening_hours"] = self.parse_hours(shop.get("hours") or {})

        apply_category(Categories.SHOP_MOBILE_PHONE, item)

        return item

    @staticmethod
    def parse_hours(hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day, times in hours.items():
            # The weekdays are joined by a "holiday" entry for public holidays, which
            # sanitise_day returns None for because OpeningHours has no day to put it on.
            if not (weekday := sanitise_day(day)):
                continue
            # `reception_time` beside it is a 受付時間 desk cut-off, not the shop's own hours.
            opening, _, closing = str((times or {}).get("business_hours") or "").partition("～")
            if opening and closing:
                opening_hours.add_range(weekday, opening.strip(), closing.strip())
        return opening_hours
