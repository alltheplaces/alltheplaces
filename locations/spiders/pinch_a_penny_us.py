from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class PinchAPennyUSSpider(SitemapSpider, StructuredDataSpider):
    name = "pinch_a_penny_us"
    item_attributes = {"brand": "Pinch A Penny", "brand_wikidata": "Q121436109"}
    sitemap_urls = ["https://pinchapenny.com/sitemap.xml"]
    sitemap_rules = [(r"com/stores/[^\\]+\-\w\w\-(\d+)$", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()

        yield item
