from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser


class ArnoldClarkSpider(SitemapSpider):
    name = "arnold_clark"
    item_attributes = {
        "brand": "Arnold Clark",
        "brand_wikidata": "Q29344371",
    }
    sitemap_urls = ["https://www.arnoldclark.com/sitemap/branch.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.arnoldclark\.com\/find-a-dealer\/([-\w]+)\/ref\/([-\w]+)$",
            "parse_item",
        )
    ]

    def parse_item(self, response):
        item = LinkedDataParser.parse(response, "AutoDealer")
        apply_category(Categories.SHOP_CAR, item)
        return item
