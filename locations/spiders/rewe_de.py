from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class REWEDESpider(SitemapSpider, StructuredDataSpider):
    name = "rewe_de"
    item_attributes = {"brand": "REWE", "brand_wikidata": "Q16968817", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.rewe.de"]
    sitemap_urls = ["https://www.rewe.de/sitemaps/sitemap-maerkte.xml"]
    sitemap_rules = [(r"^https:\/\/www\.rewe\.de\/marktseite\/[\w\-]+\/\d+\/[\w\-]+\/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["street_address"] = item["street_address"].removesuffix(" null")
        item.pop("image", None)
        yield item
