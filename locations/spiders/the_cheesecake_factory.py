from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TheCheesecakeFactorySpider(SitemapSpider, StructuredDataSpider):
    name = "the_cheesecake_factory"
    item_attributes = {"brand": "The Cheesecake Factory", "brand_wikidata": "Q1045842"}
    sitemap_urls = ["https://locations.thecheesecakefactory.com/sitemap_0.xml"]

    # store URLs are ones ending in .html
    sitemap_rules = [(r".*\.html$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # the following values are not unique to each store
        item.pop("twitter")
        item.pop("facebook")
        item.pop("image")
        yield item