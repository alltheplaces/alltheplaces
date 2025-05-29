from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TriumphSpider(SitemapSpider, StructuredDataSpider):
    name = "triumph"
    item_attributes = {"brand": "Triumph", "brand_wikidata": "Q671216"}
    allowed_domains = ["storelocator.triumph.com"]
    sitemap_urls = ["https://storelocator.triumph.com/en/sitemap.xml"]
    sitemap_rules = [(r"/en/.+/triumph-[-\w]+-(\d+)/?$", "parse_sd")]

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data.pop("@id", None)  # capture store id as ref instead of website
