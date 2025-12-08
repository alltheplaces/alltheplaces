from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TheContainerStoreSpider(SitemapSpider, StructuredDataSpider):
    name = "the_container_store"
    item_attributes = {"brand": "The Container Store", "brand_wikidata": "Q7727445"}
    sitemap_urls = ["https://www.containerstore.com/stores/sitemap1.xml"]
    sitemap_rules = [(r"/stores/", "parse")]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("The Container Store ")
        yield item
