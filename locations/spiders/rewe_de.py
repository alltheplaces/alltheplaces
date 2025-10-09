from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class ReweDESpider(SitemapSpider, StructuredDataSpider, PlaywrightSpider):
    name = "rewe_de"
    item_attributes = {"name": "Rewe", "brand": "Rewe", "brand_wikidata": "Q16968817"}
    allowed_domains = ["www.rewe.de"]
    sitemap_urls = ["https://www.rewe.de/sitemaps/sitemap-maerkte.xml"]
    sitemap_rules = [(r"/marktseite/[^/]+/(\d+)/[^/]+/$", "parse_sd")]
    # Playwright needed to avoid blocking from certain IP address ranges.
    # Probably use of data centre IPs is the main reason.
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def post_process_item(self, item, response, ld_data):
        item["name"] = None
        item["street_address"] = item["street_address"].removesuffix(" null")
        item.pop("image", None)

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
