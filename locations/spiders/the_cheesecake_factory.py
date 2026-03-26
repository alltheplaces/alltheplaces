from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TheCheesecakeFactorySpider(SitemapSpider, StructuredDataSpider):
    name = "the_cheesecake_factory"
    item_attributes = {"brand": "The Cheesecake Factory", "brand_wikidata": "Q1045842"}
    sitemap_urls = ["https://locations.thecheesecakefactory.com/sitemap_0.xml"]
    sitemap_rules = [(r".*\-(\d+)\.html$", "parse_sd")]
    drop_attributes = {"image"}
    search_for_twitter = False
    search_for_facebook = False
    search_for_image = False
