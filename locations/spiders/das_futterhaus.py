from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DasFutterhausSpider(SitemapSpider, StructuredDataSpider):
    name = "das_futterhaus"
    item_attributes = {"brand": "Das Futterhaus", "brand_wikidata": "Q1167914"}
    sitemap_urls = ["https://www.futterhaus.de/sitemap.xml"]
    sitemap_rules = [(r"/service/filialen/", "parse_sd")]
    skip_auto_cc_domain = True
