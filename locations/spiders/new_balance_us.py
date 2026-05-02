from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider

class NewBalanceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "new_balance_us"
    item_attributes = {"brand": "New Balance", "brand_wikidata": "Q742988"}
    sitemap_urls = ["https://stores.newbalance.com/sitemap.xml"]
    # matches store urls while excluding spanish translation pages
    sitemap_rules = [(r"^https://stores\.newbalance\.com/(?!es/)[^/]+/[^/]+/[^/]+/?$", "parse_sd"),]

    search_for_facebook = False
    search_for_twitter = False