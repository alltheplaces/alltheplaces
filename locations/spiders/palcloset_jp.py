from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class PalclosetJPSpider(Spider):
    name = "palcloset_jp"

    start_urls = ["https://palcloset.storelocator.jp/api/point/x/"]
    allowed_domains = ["palcloset.storelocator.jp"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            match store["extra_fields"]["代表ブランド名"]:
                case "3COINS":
                    item.update({"brand_wikidata": "Q60997353"})
                    apply_category(Categories.SHOP_VARIETY_STORE, item)
                case _:
                    item["brand"] = store["extra_fields"]["代表ブランド名"]
                    apply_category(Categories.SHOP_CLOTHES, item)

            item["website"] = (
                f"https://www.palcloset.jp/addons/pal/shoplist/detail/?brandshop_no={store['key']}&b={store['extra_fields']['代表ブランドコード']}"
            )
            item["postcode"] = store["extra_fields"]["郵便番号"]
            if store["extra_fields"]["電話番号"] != "-":
                item["phone"] = f"+81 {store['extra_fields']['電話番号']}"
            item["extras"]["addr:province"] = store["extra_fields"]["都道府県"]
            item["branch"] = store["name"]
            item["name"] = None
            yield item
