from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BobJaneTmartsAUSpider(SitemapSpider, StructuredDataSpider):
    name = "bob_jane_tmarts_au"
    item_attributes = {"brand_wikidata": "Q16952468"}
    allowed_domains = ["www.bobjane.com.au"]
    sitemap_urls = ["https://www.bobjane.com.au/sitemaps/public/store_search.xml.gz"]
    sitemap_rules = [
        (r"shop/.*$", "parse_sd"),
    ]
