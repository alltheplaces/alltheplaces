from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TheGoodFeetStoreUSSpider(SitemapSpider, StructuredDataSpider):
    name = "the_good_feet_store_us"
    item_attributes = {"brand": "The Good Feet Store", "brand_wikidata": "Q122031157"}
    allowed_domains = ["www.goodfeet.com"]
    sitemap_urls = ["https://www.goodfeet.com/sitemap.xml"]
    sitemap_rules = [(r"\/locations\/[a-z]{2}\/[\w\-]+$", "parse_sd")]
    wanted_types = ["LocalBusiness", "ShoeStore"]
    download_delay = 0.2

    def post_process_item(self, item, response, ld_data):
        item.pop("facebook", None)
        item.pop("twitter", None)
        item["website"] = response.url
        yield item
