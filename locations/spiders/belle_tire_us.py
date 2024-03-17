from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BelleTireUSSpider(SitemapSpider, StructuredDataSpider):
    name = "belle_tire_us"
    item_attributes = {"brand": "Belle Tire", "brand_wikidata": "Q16984061"}
    sitemap_urls = ["https://www.belletire.com/sitemap-index.xml"]
    sitemap_rules = [(r"https://www.belletire.com/stores/detail/\d+/[\w-]+", "parse_sd")]
