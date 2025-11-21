from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TheGoodGuysAUSpider(SitemapSpider, StructuredDataSpider):
    name = "the_good_guys_au"
    item_attributes = {"brand": "The Good Guys", "brand_wikidata": "Q7737217"}
    sitemap_urls = ["https://www.thegoodguys.com.au/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]
