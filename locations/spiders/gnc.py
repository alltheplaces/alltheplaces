from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GncSpider(SitemapSpider, StructuredDataSpider):
    name = "gnc"
    item_attributes = {"brand": "GNC", "brand_wikidata": "Q4808595"}
    download_delay = 5
    sitemap_urls = ("https://stores.gnc.com/sitemap.xml",)
    sitemap_rules = [
        (r"^https://stores.gnc.com/all-stores-[^/]+/[^/]+/[^/]+$", "parse_sd"),
    ]
    wanted_types = ["HobbyShop"]
