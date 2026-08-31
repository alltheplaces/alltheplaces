from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class ZeemanSpider(SitemapSpider, StructuredDataSpider):
    name = "zeeman"
    item_attributes = {"brand": "Zeeman", "brand_wikidata": "Q184399"}
    sitemap_urls = ["https://www.zeeman.com/robots.txt"]
    sitemap_follow = ["/nl-nl/sitemap/stores.xml"]
    sitemap_rules = [("/nl-nl/stores/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["extras"]["website:nl"] = response.url
        item["extras"]["website:be"] = response.url.replace(".com/nl-nl/winkels", ".com/nl-be/winkels")
        item["extras"]["website:fr"] = response.url.replace(".com/nl-nl/winkels", ".com/fr-fr/magasins")
        item["extras"]["website:de"] = response.url.replace(".com/nl-nl/winkels", ".com/de-de/shops")
        item["extras"]["website:es"] = response.url.replace(".com/nl-nl/winkels", ".com/es-es/tiendas")
        item["extras"]["website:pt"] = response.url.replace(".com/nl-nl/winkels", ".com/pt-pt/lojas")

        if item.get("twitter") == "zeeman.com":
            item.pop("twitter")
        if item.get("facebook") and "zeemantextielsupers" in item["facebook"]:
            item.pop("facebook")

        item["branch"] = item["branch"].removeprefix("Zeeman ")

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
