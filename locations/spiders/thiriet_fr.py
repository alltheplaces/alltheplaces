from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ThirietFRSpider(StructuredDataSpider):
    name = "thiriet_fr"
    item_attributes = {"brand": "Thiriet", "brand_wikidata": "Q3524695"}
    start_urls = ["https://www.thiriet.com/sitemap2.txt"]

    def parse(self, response, **kwargs):
        for url in response.text.splitlines():
            yield response.follow(url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["website"] = item["ref"] = response.url.split("?", 1)[0]
        item["name"] = None
        apply_category(Categories.SHOP_FROZEN_FOOD, item)
        yield item
