from scrapy import Spider
from scrapy.http import JsonRequest

from locations.items import Feature
from locations.spiders.kia_au import KiaAUSpider


class KiaKRSpider(Spider):
    name = "kia_kr"
    item_attributes = KiaAUSpider.item_attributes
    allowed_domains = ["kwpapi.kia.com", "kia.com"]
    start_urls = ["https://www.kia.com/kr/experience/branch"]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "window.KWPGlobal = {")]/text()').get()
        auth_token = js_blob.split("token: '", 1)[1].split("'", 1)[0].replace("\\u002D", "-")
        yield JsonRequest(
            url="https://kwpapi.kia.com/kr/ko/api/v1/experience/sales-network/branchs?limitDistance=30000&latitude=37.4643623227152&longitude=127.042663599215",
            headers={"Ccsp-Authorization": "Bearer", "X-SYSTEM-AUTHORIZATION": f"Bearer {auth_token}"},
            callback=self.parse_locations,
        )

    def parse_locations(self, response):
        for location in response.json()["body"]:
            properties = {
                "ref": location["brchstId"],
                "name": location["brchstName"],
                "lat": location["brchstLatit"],
                "lon": location["brchstLngt"],
                "addr_full": location["brchstAddr"],
                "postcode": location["brchstZipcd"],
                "phone": location["brchstTelno"],
            }
            yield Feature(**properties)
