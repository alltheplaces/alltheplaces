from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class SaqCASpider(Spider):
    name = "saq_ca"
    item_attributes = {"brand": "SAQ", "brand_wikidata": "Q3488077"}

    def make_request(self, page: int) -> JsonRequest:
        return JsonRequest(
            url="https://www.saq.com/en/store/locator/ajaxlist/?loaded={}".format(page),
            headers={"X-Requested-With": "XMLHttpRequest"},
            cb_kwargs={"content_loaded": page},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        if data["list"] not in ["None", None, "", []]:
            for shop in data["list"]:
                item = DictParser.parse(shop)
                item["branch"] = item.pop("name")
                apply_category(Categories.SHOP_ALCOHOL, item)
                yield item
            content_loaded = kwargs["content_loaded"] + 10
            yield self.make_request(content_loaded)
