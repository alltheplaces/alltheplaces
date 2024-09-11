from locations.structured_data_spider import StructuredDataSpider


class VandenBorreBESpider(StructuredDataSpider):
    name = "vanden_borre_be"
    item_attributes = {"brand": "Vanden Borre", "brand_wikidata": "Q3554485"}
    start_urls = ["https://www.vandenborre.be/web/json/shops_NL.json"]

    def parse(self, response, **kwargs):
        for store in response.json()["markers"]:
            yield response.follow(store["url"], self.parse_sd)
