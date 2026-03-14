from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class OldWildWestSpider(SitemapSpider, StructuredDataSpider):
    name = "old_wild_west"
    item_attributes = {"brand": "Old Wild West", "brand_wikidata": "Q25402475"}
    sitemap_urls = ["https://www.oldwildwest.it/sitemap-index.xml"]
    sitemap_rules = [("/it/ristoranti/", "parse_sd")]
    skip_auto_cc_domain = True
