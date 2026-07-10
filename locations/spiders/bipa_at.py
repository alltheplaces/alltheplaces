import base64
import hashlib
import json
import secrets
from typing import Any, AsyncIterator, Iterable
from urllib.parse import parse_qs, urlencode, urlparse

from scrapy import Request, Spider
from scrapy.http import FormRequest, JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature

ORGANIZATION_ID = "f_ecom_aaft_prd"
CLIENT_ID = "2f55a356-1392-4de0-9cdf-f74f0666f43d"
SITE_ID = "AT"
API = "https://www.bipa.at/mobify/proxy/api"
REDIRECT_URI = "https://www.bipa.at/callback"
PAGE_SIZE = 200


class BipaATSpider(Spider):
    name = "bipa_at"
    item_attributes = {"brand": "Bipa", "brand_wikidata": "Q864933"}

    async def start(self) -> AsyncIterator[Request]:
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
        challenge = base64.urlsafe_b64encode(hashlib.sha256(self.code_verifier.encode()).digest()).rstrip(b"=").decode()
        query = urlencode(
            {
                "client_id": CLIENT_ID,
                "channel_id": SITE_ID,
                "code_challenge": challenge,
                "hint": "guest",
                "response_type": "code",
                "redirect_uri": REDIRECT_URI,
            }
        )
        yield Request(
            f"{API}/shopper/auth/v1/organizations/{ORGANIZATION_ID}/oauth2/authorize?{query}",
            callback=self.parse_authorization,
            meta={"dont_redirect": True, "handle_httpstatus_list": [302, 303]},
        )

    def parse_authorization(self, response: Response) -> Iterable[FormRequest]:
        query = parse_qs(urlparse(response.headers["Location"].decode()).query)
        yield FormRequest(
            f"{API}/shopper/auth/v1/organizations/{ORGANIZATION_ID}/oauth2/token",
            formdata={
                "grant_type": "authorization_code_pkce",
                "code": query["code"][0],
                "usid": query["usid"][0],
                "code_verifier": self.code_verifier,
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "channel_id": SITE_ID,
            },
            callback=self.parse_token,
        )

    def parse_token(self, response: Response) -> Iterable[JsonRequest]:
        yield self.store_search(response.json()["access_token"], 0)

    def store_search(self, token: str, offset: int) -> JsonRequest:
        query = urlencode(
            {
                "countryCode": SITE_ID,
                "distanceUnit": "km",
                "latitude": 47.7,
                "longitude": 13.35,
                "maxDistance": 1000,
                "siteId": SITE_ID,
                "limit": PAGE_SIZE,
                "offset": offset,
            }
        )
        return JsonRequest(
            f"{API}/store/shopper-stores/v1/organizations/{ORGANIZATION_ID}/store-search?{query}",
            headers={"Authorization": f"Bearer {token}"},
            meta={"token": token, "offset": offset},
            callback=self.parse_stores,
        )

    def parse_stores(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()
        for store in data["data"]:
            hours = json.loads(store.pop("storeHours", None) or "{}")
            item = DictParser.parse(store)
            item.pop("name", None)
            item.pop("country", None)  # source countryCode is unreliable (some AT stores tagged GB)
            item["ref"] = store["id"]
            item["street_address"] = store.get("address1")
            item["opening_hours"] = OpeningHours()
            for day, times in hours.items():
                for time_range in times if isinstance(times, list) else [times]:
                    if " - " in (time_range or ""):
                        item["opening_hours"].add_range(day, *time_range.split(" - "))
            apply_category(Categories.SHOP_CHEMIST, item)
            yield item

        offset = response.meta["offset"] + PAGE_SIZE
        if offset < data["total"]:
            yield self.store_search(response.meta["token"], offset)
