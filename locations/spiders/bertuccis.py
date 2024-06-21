from chompjs import chompjs
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser


class BertuccisSpider(SitemapSpider):
    name = "bertuccis"
    item_attributes = {"brand": "Bertucci's", "brand_wikidata": "Q4895917"}
    sitemap_urls = ["https://www.bertuccis.com/ee-locations-sitemap.xml"]
    sitemap_rules = [
        (r"/locations/", "parse"),
    ]

    def parse(self, response):
        data = chompjs.parse_js_object(
            response.xpath(r'//*[contains(text(),"properties")]/text()').re_first(r"properties\":({.*}),\"geometry")
        )
        item = DictParser.parse(data)
        item["ref"] = item["website"] = response.url
        item["name"] = response.xpath(r"//title/text()").get()
        item["street_address"] = data.get("address_line_1")
        item["addr_full"] = data.get("address_formatted")
        yield item
