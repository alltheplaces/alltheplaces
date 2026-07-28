from typing import Any, AsyncIterator
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature

ADDRESS_URL = "https://www.baskinrobbins.co.kr/api/store-address.php"
STORES_URL = "https://www.baskinrobbins.co.kr/api/store-list.php"
RESULT_LIMIT = 100


class BaskinRobbinsKRSpider(Spider):
    name = "baskin_robbins_kr"
    item_attributes = {"brand_wikidata": "Q584601"}

    async def start(self) -> AsyncIterator[Request]:
        self.seen_refs: set[str] = set()
        yield Request(ADDRESS_URL, callback=self.parse_regions)

    def parse_regions(self, response: Response, **kwargs: Any) -> Any:
        for entry in response.json()["result"]["list"]:
            yield self.make_request(entry["address"])

    def parse_stores(self, response: Response, sido: str, gugun: str | None = None) -> Any:
        result = response.json()["result"]

        if result["cnt"] >= RESULT_LIMIT:
            if gugun is None:
                yield Request(
                    f"{ADDRESS_URL}?{urlencode({'sido': sido})}",
                    callback=self.parse_districts,
                    cb_kwargs={"sido": sido},
                )
                return
            self.logger.warning("Store results for %s, %s reached the API limit of %d", sido, gugun, RESULT_LIMIT)

        for store in result["list"] or []:
            if store["store_code"] in self.seen_refs:
                continue
            self.seen_refs.add(store["store_code"])

            item = Feature()
            item["ref"] = store["store_code"]
            item["branch"] = store["store_name"]
            item["phone"] = store["local_no"]
            item["lat"] = store["latitude"]
            item["lon"] = store["longitude"]
            item["state"] = store["addr_si"]
            item["city"] = store["addr_gugun"]
            item["addr_full"] = " ".join(
                part.strip()
                for key in ["addr_si", "addr_gugun", "addr_road", "addr_detail"]
                if (part := store.get(key))
            )

            services = store.get("service_info") or ""
            apply_yes_no(Extras.TAKEAWAY, item, "픽업" in services)
            apply_yes_no(Extras.DELIVERY, item, "배달" in services)

            yield item

    def parse_districts(self, response: Response, sido: str) -> Any:
        for entry in response.json()["result"]["list"]:
            yield self.make_request(sido, entry["address"])

    def make_request(self, sido: str, gugun: str | None = None) -> Request:
        params = {"sido": sido}
        if gugun:
            params["gugun"] = gugun
        return Request(
            f"{STORES_URL}?{urlencode(params)}",
            callback=self.parse_stores,
            cb_kwargs={"sido": sido, "gugun": gugun},
        )
