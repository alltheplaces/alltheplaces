from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GrandOpticalSpider(SitemapSpider, StructuredDataSpider):
    name = "grand_optical"
    item_attributes = {"brand": "GrandOptical", "brand_wikidata": "Q3113677"}
    sitemap_urls = ["https://www.grandoptical.com/sitemap.xml"]
    sitemap_rules = [(r"/opticien/[^/]+/\d+", "parse_sd")]
