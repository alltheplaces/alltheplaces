import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class FlannelsGBSpider(SitemapSpider, StructuredDataSpider):
    name = "flannels_gb"
    item_attributes = {"brand": "Flannels", "brand_wikidata": "Q18160381"}
    sitemap_urls = ["https://www.flannels.com/sitemap-store-pages.xml"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        # Take structured data as well as embedded JSON to form a better POI.
        json = chompjs.parse_js_object(response.xpath('//script[contains(text(),"var store = ")]/text()').get())
        json_item = DictParser.parse(json)
        item["lat"] = json_item["lat"]
        item["lon"] = json_item["lon"]
        item["street_address"] = json_item["addr_full"]
        item["city"] = json_item["city"]
        # There are a few "IE" stores.
        item["country"] = json_item["country"]
        yield item
