from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ZeemanSpider(SitemapSpider, StructuredDataSpider):
    name = "zeeman"
    item_attributes = {"brand": "Zeeman", "brand_wikidata": "Q184399"}
    sitemap_urls = ["https://www.zeeman.com/robots.txt"]
    sitemap_rules = [("com/nl-nl/stores/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["extras"]["website:nl"] = response.url
        item["extras"]["website:de"] = response.url.replace("com/nl/store", "com/de/store")
        item["extras"]["website:fr"] = response.url.replace("com/nl/store", "com/fr/store")
        item["extras"]["website:es"] = response.url.replace("com/nl/store", "com/es/store")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
