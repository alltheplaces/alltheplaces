from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BeallsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "bealls_us"
    item_attributes = {"brand": "Bealls", "brand_wikidata": "Q4876153"}
    sitemap_urls = ["https://stores.bealls.com/robots.txt"]
    sitemap_rules = [(r"\.com/\w\w/[^/]+/clothing-store-(\d+)\.html$", "parse")]
    wanted_types = ["ClothingStore"]
    search_for_email = False

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["name"] = None
