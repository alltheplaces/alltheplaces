from scrapy import Spider

from locations.dict_parser import DictParser


class MamasAndPapasGBSpider(Spider):
    name = "mamas_and_papas_gb"
    item_attributes = {"brand": "Mamas & Papas", "brand_wikidata": "Q6745447"}
    start_urls = ["https://cdn.shopify.com/s/files/1/0414/6023/6453/t/1/assets/sca.storelocatordata.json"]

    def parse(self, response, **kwargs):
        for store in response.json():
            if store.get("tagsvalue") != "Store":
                continue

            store["street_address"] = store.pop("address")
            if store.get("address2"):
                store["street_address"] += ", " + store.pop("address2")

            item = DictParser.parse(store)

            item["website"] = store.get("web")

            # TODO: Sometimes located in Next

            yield item
