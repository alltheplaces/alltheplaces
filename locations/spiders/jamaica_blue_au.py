from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class JamaicaBlueAUSpider(SitemapSpider, StructuredDataSpider):
    name = "jamaica_blue_au"
    item_attributes = {"brand": "Jamaica Blue", "brand_wikidata": "Q24965819"}
    sitemap_urls = ["https://jamaicablue.com.au/stores-sitemap.xml"]
    wanted_types = ["CafeOrCoffeeShop"]
    time_format = "%I:%M%p"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath("//@lat").get()
        item["lon"] = response.xpath("//@lng").get()
        yield item
