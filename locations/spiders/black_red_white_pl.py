from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BlackRedWhitePLSpider(SitemapSpider, StructuredDataSpider):
    name = "black_red_white_pl"
    item_attributes = {"brand": "Black Red White", "brand_wikidata": "Q4921546"}
    sitemap_urls = ["https://www.brw.pl/sitemap/salony.xml"]

    def pre_process_data(self, ld_data, **kwargs):
        ld_data["@id"] = None

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        yield item
