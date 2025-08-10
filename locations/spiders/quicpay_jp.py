import unicodedata

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class quicpayJPSpider(scrapy.Spider):
    name = "quicpay_jp"
    country_code = "JP"

    KIND = {
        1: Categories.SHOP_CONVENIENCE,
        2: Categories.FUEL_STATION,
        3: Categories.SHOP_SUPERMARKET,
        4: Categories.SHOP_CHEMIST,
        5: Categories.RESTAURANT,
        6: Categories.GENERIC_SHOP,
        7: Categories.SHOP_ELECTRONICS,
        8: Categories.SHOP_DEPARTMENT_STORE,
        9: Categories.GENERIC_SHOP,
        10: Categories.GENERIC_SHOP,
        11: Categories.GENERIC_POI,
        12: Categories.CAFE,
        13: Categories.PUB,
        14: Categories.FAST_FOOD,
        15: Categories.GENERIC_POI,
        16: Categories.SHOP_BOOKS,
        17: Categories.GENERIC_SHOP,
    }

    def start_requests(self):
        yield self.get_page(1)

    def get_page(self, n):
        return scrapy.Request(
            f"https://api-branddb.jcb.jp/api/stores_qp?page={n}",
            meta={"page": n},
        )

    def parse(self, response):
        data = response.json()
        stores = data["result"]

        for store in stores:
            item = DictParser.parse(store)
            store_type = store["genre"]["id"]
            item["name"] = unicodedata.normalize("NFKC", str(store["locationNameLocal"]))
            item["extras"]["name:ja-Hira"] = unicodedata.normalize("NFKC", str(store["locationNameKana"]))
            # item["website"] = f"https://www.quicpay.jp/shoplist/search/?page=map&detail={store['id']}" #gives 404 when not accessing from within map results

            apply_category(self.KIND.get(store_type), item)

            item["street_address"] = merge_address_lines([store["address1"], store["address2"], store["address3"]])
            item["extras"]["payment:quicpay"] = "yes"
            yield item

        if data["page"] < 2:  # if data["page"] < data["totalCount"]:
            yield self.get_page(1 + response.meta["page"])
