import re

from scrapy import Request, Selector

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class KookaiFRSpider(JSONBlobSpider):
    name = "kookai_fr"
    item_attributes = {
        "brand": "Kookaï",
        "brand_wikidata": "Q1783759",
    }
    start_urls = [
        "https://kookai.fr/apps/store-locator/stores/surrounding?shop=kookai-amh.myshopify.com&latitude=48.26417&longitude=6.169246&max_distance=0&limit=0&calc_distance=0&record_search=0&distance_unit=KM&store_name_like="
    ]

    locations_key = "stores"

    def post_process_item(self, item, response, location):
        apply_category(Categories.SHOP_CLOTHES, item)

        selector = Selector(text=location["summary"])
        item["branch"] = (selector.css(".sl-layout-line--name ::text").get() or "").removeprefix("KOOKAI ")
        item["name"] = "Kookaï"
        item["street_address"] = selector.css(".sl-layout-line--address ::text").get() or ""
        item["addr_full"] = (
            item["street_address"] + ", " + (selector.css(".sl-layout-line--country ::text").get() or "")
        )

        match = re.search(r"\b\d{4,5}\b", item["addr_full"])
        item["postcode"] = match.group().zfill(5) if match else None
        item["country"] = "FR"

        yield Request(
            "https://kookai.fr/apps/store-locator/stores/info?shop=kookai-amh.myshopify.com&data=detailed&store_id="
            + str(location["store_id"]),
            callback=self.parse_store_detail,
            errback=lambda self, response : (yield response.meta["item"]),
            meta={"item": item},
        )

    def parse_store_detail(self, response):
        item = response.meta["item"]

        data = response.json()
        try:
            selector = Selector(text=data["data"])

            item["phone"] = selector.css(".sl-layout-line--phone ::text").get() or ""
            item["email"] = selector.css(".sl-layout-line--email ::text").get() or ""
        except KeyError:
            pass

        yield item
