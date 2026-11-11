from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class FurnmartSpider(SitemapSpider, StructuredDataSpider):
    name = "furnmart"
    item_attributes = {"brand": "Furnmart", "brand_wikidata": "Q118185771"}

    sitemap_urls = [
        "https://www.furnmart.co.za/sitemap_stores.xml",
        "https://www.furnmart.com.na/sitemap_stores.xml",
        "https://www.furnmart.co.bw/sitemap_stores.xml",
    ]
    sitemap_rules = [("/stores/", "parse_sd")]
