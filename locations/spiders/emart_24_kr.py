from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT

API_URL = "https://emart24.co.kr/api1/store?page={}"
PAGE_SIZE = 40


class Emart24KRSpider(Spider):
    name = "emart_24_kr"
    item_attributes = {"brand_wikidata": "Q16219674"}
    allowed_domains = ["emart24.co.kr"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": BROWSER_DEFAULT,
    }
    requires_proxy = "KR"

    async def start(self) -> AsyncIterator[Request]:
        yield self.store_request(1)

    def store_request(self, page: int) -> Request:
        return Request(API_URL.format(page), cb_kwargs={"page": page})

    def parse(self, response: Response, page: int, **kwargs: Any) -> Any:
        data = response.json()
        for store in data["data"]:
            item = DictParser.parse(store)
            item["ref"] = str(store["CODE"])
            item["branch"] = item.pop("name", None) or store.get("TITLE")

            address = store.get("ADDRESS")
            if address:
                address_detail = store.get("ADDRESS_DE")
                if address_detail and address_detail.strip() != "-":
                    item["addr_full"] = f"{address} {address_detail}"

                address_parts = address.split(maxsplit=2)
                item["state"] = address_parts[0]
                if len(address_parts) > 1 and address_parts[1].endswith(("시", "군", "구")):
                    item["city"] = address_parts[1]

            if store.get("SVR_24") == 1:
                item["opening_hours"] = "24/7"

            yield item

        if page == 1:
            total_pages = (data["count"] + PAGE_SIZE - 1) // PAGE_SIZE
            for next_page in range(2, total_pages + 1):
                yield self.store_request(next_page)
