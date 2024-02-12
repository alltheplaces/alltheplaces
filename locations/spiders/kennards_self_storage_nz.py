from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KennardsSelfStorageNZSpider(SitemapSpider, StructuredDataSpider):
    name = "kennards_self_storage_nz"
    item_attributes = {"brand": "Kennards Self Storage", "brand_wikidata": "Q115565997"}
    sitemap_urls = ["https://www.kennards.co.nz/sitemap.xml"]
    sitemap_rules = [("locations/(.*)$", "parse_sd")]
