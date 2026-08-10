from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DennysUSSpider(SitemapSpider, StructuredDataSpider):
    name = "dennys_us"
    item_attributes = {"brand": "Denny's", "brand_wikidata": "Q1189695"}
    sitemap_urls = ["https://locations.dennys.com/robots.txt"]
    sitemap_rules = [(r"https://locations.dennys.com/[^/]+/[^/]+/(\d+)$", "parse_sd")]
    search_for_twitter = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = None

        if any("Coming Soon!" in t for t in response.css(".location-info ::text").getall()):
            return

        item["extras"]["website:menu"] = response.xpath('//a[@data-event-name="loc_view_menu"]/@href').get()
        item["extras"]["website:orders"] = response.xpath('//a[@data-event-name="loc_order_online"]/@href').get()

        yield item
