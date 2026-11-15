from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

LOCALES = {
    "AT": "de-at/shops",
    "BE": "nl-be/winkels",
    "DE": "de-de/shops",
    "ES": "es-es/tiendas",
    "FR": "fr-fr/magasins",
    "LU": "fr-lu/magasins",
    "NL": "nl-nl/winkels",
}


class ZeemanSpider(SitemapSpider, StructuredDataSpider):
    name = "zeeman"
    item_attributes = {"brand": "Zeeman", "brand_wikidata": "Q184399"}
    sitemap_urls = ["https://www.zeeman.com/robots.txt"]
    sitemap_follow = ["/nl-nl/sitemap/stores.xml"]
    sitemap_rules = [("/nl-nl/winkels/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["website"] = response.url.replace("nl-nl/winkels", LOCALES[item["country"]])
        if item["country"] == "BE":
            item["extras"]["website:nl"] = item["website"]
            item["extras"]["website:fr"] = response.url.replace("nl-nl/winkels", "fr-be/magasins")

        if item.get("twitter") == "zeeman.com":
            item.pop("twitter")
        if item.get("facebook") and "zeemantextielsupers" in item["facebook"]:
            item.pop("facebook")

        item["branch"] = item["branch"].removeprefix("Zeeman ")

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
