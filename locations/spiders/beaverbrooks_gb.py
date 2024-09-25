import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.structured_data_spider import StructuredDataSpider


class BeaverbrooksGBSpider(CrawlSpider,StructuredDataSpider):
    name = "beaverbrooks_gb"
    item_attributes = {"brand": "Beaverbrooks", "brand_wikidata": "Q4878226"}
    start_urls = [
        "https://www.beaverbrooks.co.uk/stores",
    ]
    rules = [
        Rule(LinkExtractor(r"https://www.beaverbrooks.co.uk/stores/([-\w]+)$"), "parse"),
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"]=response.xpath('//div[@id="map_canvas"]/@data-lat').get()
        item["lon"]=response.xpath('//div[@id="map_canvas"]/@data-long').get()
        yield item
