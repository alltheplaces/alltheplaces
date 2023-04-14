import scrapy

from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class BiggbySpider(scrapy.Spider):
    name = "biggby"
    item_attributes = {"brand": "Biggby Coffee", "brand_wikidata": "Q4906876"}
    allowed_domains = ["www.biggby.com"]
    start_urls = ("https://www.biggby.com/locations/",)

    def parse(self, response):
        for location in response.xpath('//div[@id="content"]/markers/marker'):
            item = DictParser.parse(location.attrib)
            item["street_address"] = clean_address([location.attrib["address-one"], location.attrib["address-two"]])

            yield item
