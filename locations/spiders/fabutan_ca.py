from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FabutanCASpider(SitemapSpider, StructuredDataSpider):
    name = "fabutan_ca"
    item_attributes = {"brand_wikidata": "Q120765494"}
    sitemap_urls = ["https://fabutan.com/sitemap.xml"]
    sitemap_rules = [
        (
            r"/locations/[\w-]+/[\w-]+/[\w-]+/$",
            "parse_sd",
        )
    ]
