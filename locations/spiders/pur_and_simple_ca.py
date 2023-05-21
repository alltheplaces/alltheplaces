from scrapy import Spider

from locations.items import Feature


class PurAndSimpleCASpider(Spider):
    name = "pur_and_simple_ca"
    item_attributes = {"brand": "Pür & Simple", "brand_wikidata": "Q118558630"}
    start_urls = ["https://pursimple.com/locations/"]

    def parse(self, response, **kwargs):
        for location in response.xpath('//div[@class="list_item"]'):
            item = Feature()
            item["ref"] = item["website"] = location.xpath(".//a/@href").get()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-lng").get()
            item["name"] = location.xpath(".//a/text()").get()
            item["addr_full"] = location.xpath(".//p/text()").get()

            yield item
