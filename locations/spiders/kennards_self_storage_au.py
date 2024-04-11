from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class KennardsSelfStorageAUSpider(SitemapSpider, StructuredDataSpider):
    name = "kennards_self_storage_au"
    item_attributes = {"brand": "Kennards Self Storage", "brand_wikidata": "Q115565997"}
    sitemap_urls = ["https://www.kss.com.au/sitemap.xml"]
    sitemap_rules = [("locations/(.*)$", "parse_sd")]
