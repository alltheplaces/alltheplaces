from scrapy import Selector, Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CyclableSpider(Spider):
    name = "cyclable"
    item_attributes = {"brand": "Cyclable", "brand_wikidata": "Q130214989", "name": "Cyclable"}
    start_urls = ["https://www.cyclable.com/magasins"]

    def parse(self, response):
        # The page's noscript tag makes the HTML parser drop the rest of the body, so parse from the first store
        stores = Selector(text=response.text[response.text.index('<div class="col-md-6 cyclable-store-item"') :])
        for store in stores.css(".cyclable-store-item"):
            item = Feature()
            item["ref"] = store.attrib["data-store-id"]
            item["branch"] = store.css(".store-name-text::text").get().removesuffix(" - CYCLABLE")
            item["email"] = store.attrib["data-store-email"]
            item["website"] = store.attrib["data-store-url"] or None
            item["phone"] = store.css(".cyclable-phone-link::attr(href)").get()
            lines = [line.strip() for line in store.css(".cyclable-store-address::text").getall() if line.strip()]
            item["street_address"] = lines[0]
            item["postcode"] = store.attrib["data-store-postcode"]
            item["city"] = store.attrib["data-store-city"]
            item["country"] = {"France": "FR", "Suisse": "CH"}[lines[-1]]
            apply_category(Categories.SHOP_BICYCLE, item)
            yield item
