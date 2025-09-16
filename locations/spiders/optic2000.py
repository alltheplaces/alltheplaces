from locations.spiders.safeway_ca import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class Optic2000Spider(SitemapSpider, StructuredDataSpider):
    name = "optic2000"
    item_attributes = {"brand": "Optic 2000", "brand_wikidata": "Q3354445"}
    sitemap_urls = ["https://opticien.optic2000.com/sitemap.xml"]
    sitemap_rules = [(r"https://opticien.optic2000.com/[^/]+/[^/]+/[^/]+/[^/]+$", "parse_sd")]
