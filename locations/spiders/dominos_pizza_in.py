from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class DominiosINSpider(SitemapSpider, StructuredDataSpider):
    name = "dominos_pizza_in"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    sitemap_urls = ["https://www.dominos.co.in/store-locations/sitemap_store.xml"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["addr_full"] = item.pop("street_address")
        item["name"] = None

        yield item
