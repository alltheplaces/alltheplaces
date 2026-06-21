from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class AeonHokkaidoJPSpider(Spider):
    name = "aeon_hokkaido_jp"
    item_attributes = {"brand": "イオン", "brand_wikidata": "Q11285951"}

    BRAND_MAPPING = {
        "01": ("イオン", "Q11285951", Categories.SHOP_SUPERMARKET),
        "02": ("イオンスーパーセンター", "Q11285970", Categories.SHOP_SUPERMARKET),
        "03": ("マックスバリュ", "Q11340427", Categories.SHOP_SUPERMARKET),
        "04": ("ザ・ビッグ", "Q11306676", Categories.SHOP_SUPERMARKET),
        "05": ("フードセンター", None, Categories.SHOP_SUPERMARKET),
        "07": ("まいばすけっと", "Q11278154", Categories.SHOP_CONVENIENCE),
        "08": ("イオンモール・専門店街", "Q11286068", Categories.SHOP_MALL),
    }

    async def start(self) -> AsyncIterator[Request]:
        yield self.make_request(0)

    def make_request(self, offset: int) -> Request:
        return Request(
            f"https://map.aeon-hokkaido.jp/ah-store/api/proxy2/shop/list?limit=200&offset={offset}",
            meta={"offset": offset},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        for store in data["items"]:
            item = Feature()
            item["ref"] = store["code"]
            item["lat"] = store["coord"]["lat"]
            item["lon"] = store["coord"]["lon"]
            item["addr_full"] = store["address_name"]
            item["postcode"] = store.get("postal_code")
            item["phone"] = store.get("phone")
            item["website"] = store.get("external_url")
            item["extras"]["branch:ja-Hira"] = store.get("ruby")

            categories = store.get("categories", [])
            cat_code = categories[0]["code"] if categories else None
            brand_info = self.BRAND_MAPPING.get(cat_code)
            if brand_info:
                brand_ja, wikidata, category = brand_info
                item["name"] = brand_ja
                item["brand"] = brand_ja
                item["brand_wikidata"] = wikidata
                item["branch"] = store["name"].removeprefix(brand_ja).strip() or None
                apply_category(category, item)
            else:
                item["name"] = store["name"]
                apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item

        count = data["count"]
        if count["offset"] + count["limit"] < count["total"]:
            yield self.make_request(count["offset"] + count["limit"])
