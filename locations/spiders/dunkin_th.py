from scrapy import Spider

from locations.items import Feature


class DunkinTHSpider(Spider):
    name = "dunkin_th"
    item_attributes = {"brand": "Dunkin'", "brand_wikidata": "Q847743"}
    start_urls = ["http://www.dunkindonuts.co.th/store"]

    def parse(self, response, **kwargs):
        for store in response.xpath('//*[contains(@id,"store")]'):
            item = Feature()
            item["ref"] = store.xpath("./@id").get()
            item["name"] = store.xpath('.//*[@class="dd-detail__address"]/*[@class="title"]/text()').get()
            item["addr_full"] = store.xpath(".//address/span/text()").get()
            yield item
