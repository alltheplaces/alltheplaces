from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SportclubARSpider(Spider):
    name = "sportclub_ar"
    item_attributes = {"brand": "SportClub", "brand_wikidata": "Q118314171"}
    custom_settings = {
        "DOWNLOAD_TIMEOUT": 120,
    }
    handle_httpstatus_list = [422]

    def make_request(self, offset: int, limit: int = 100) -> JsonRequest:
        return JsonRequest(
            url=f"https://vhzfd7sis7qzlcy63dcjgc2cqa0lovrs.lambda-url.sa-east-1.on.aws/v1/sedes?offset={offset}&limit={limit}",
            headers={
                "api-key": "SECRET_KEY",
            },
            cb_kwargs={"offset": offset, "limit": limit},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, offset: int, limit: int) -> Any:
        if results := response.json().get("response", {}).get("results", []):
            for club in results:
                item = DictParser.parse(club)
                item["geometry"] = club["location"]
                item["geometry"]["type"] = "Point"
                item["street_address"] = club.get("direccion")
                item["city"] = club.get("zona")
                item["state"] = club.get("provincia")
                item["phone"] = club.get("telefono")
                item["website"] = "https://www.sportclub.com.ar/sedes/" + club.get("slug", "")
                apply_category(Categories.GYM, item)
                yield item

        if response.status == 422:
            if detail := response.json().get("detail"):
                if limit := int(detail[0]["loc"][-2]):
                    yield self.make_request(
                        offset, limit
                    )  # Retry with limit equals to remaining records indicated by server
        else:
            total_count = response.json()["response"]["paging"]["total"]
            new_offset = offset + limit
            if new_offset < total_count:
                yield self.make_request(new_offset, limit)
