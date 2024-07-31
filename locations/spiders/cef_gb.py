import json

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.linked_data_parser import LinkedDataParser


class CefGBSpider(CrawlSpider):
    name = "cef_gb"
    item_attributes = {"brand": "City Electrical Factors", "brand_wikidata": "Q116495226"}
    start_urls = ["https://www.cef.co.uk/stores/directory"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//a[@rel="next"]')),
        Rule(LinkExtractor(allow="/stores/", restrict_xpaths='//ul[@id="directory"]'), callback="parse"),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        ld = response.xpath('//script[@type="application/ld+json"]/text()').get()
        ld = ld.replace("&quot;", '"')
        ld_item = json.loads(ld)

        item = LinkedDataParser.parse_ld(ld_item)
        item["ref"] = response.url

        extract_google_position(item, response)

        yield item
