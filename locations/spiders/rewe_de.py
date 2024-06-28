from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class REWEDESpider(SitemapSpider, StructuredDataSpider):
    name = "rewe_de"
    item_attributes = {"name": "REWE", "brand": "REWE", "brand_wikidata": "Q16968817"}
    allowed_domains = ["www.rewe.de"]
    sitemap_urls = ["https://www.rewe.de/sitemaps/sitemap-maerkte.xml"]
    sitemap_rules = [(r"/marktseite/[^/]+/(\d+)/[^/]+/$", "parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item, response, ld_data):
        item["name"] = None
        item["street_address"] = item["street_address"].removesuffix(" null")
        item.pop("image", None)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
