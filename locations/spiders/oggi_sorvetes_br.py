import html

from scrapy import Selector

from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class OggiSorvetesBRSpider(SuperStoreFinderSpider):
    name = "oggi_sorvetes_br"
    item_attributes = {"brand": "Oggi Sorvetes", "brand_wikidata": "Q118946030"}
    allowed_domains = ["oggisorvetes.com.br"]

    def parse_item(self, item: Feature, location: Selector, **kwargs):
        item["addr_full"] = html.unescape(location.xpath("./address/text()").get())
        item["postcode"] = location.xpath("./zip/text()").get()
        item["country"] = location.xpath("./country/text()").get()

        if phone := item.get("phone"):
            item["phone"] = phone.replace("ou", ";")

        yield item
