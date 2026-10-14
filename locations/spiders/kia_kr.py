from typing import AsyncIterator

from scrapy import FormRequest, Request, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.kia_au import KiaAUSpider


class KiaKRSpider(Spider):
    name = "kia_kr"
    item_attributes = KiaAUSpider.item_attributes
    allowed_domains = ["kwpapi.kia.com", "kia.com", "members.kia.com"]

    async def start(self) -> AsyncIterator[Request]:
        yield Request(url="https://www.kia.com/kr/experience/branch", callback=self.parse_auth_token)
        yield FormRequest(
            url="https://members.kia.com/kr/knet/searchAsaList.do",
            formdata={"currpage": "1", "pagesize": "2000"},
            headers={"X-Requested-With": "XMLHttpRequest"},
            callback=self.parse_service_centres,
        )

    def parse_auth_token(self, response):
        js_blob = response.xpath('//script[contains(text(), "window.KWPGlobal = {")]/text()').get()
        auth_token = js_blob.split("token: '", 1)[1].split("'", 1)[0].replace("\\u002D", "-")
        yield JsonRequest(
            url="https://kwpapi.kia.com/kr/ko/api/v1/experience/sales-network/branchs?limitDistance=30000&latitude=37.4643623227152&longitude=127.042663599215",
            headers={"Ccsp-Authorization": "Bearer", "X-SYSTEM-AUTHORIZATION": f"Bearer {auth_token}"},
            callback=self.parse_dealerships,
        )

    def parse_dealerships(self, response):
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
            item = Feature(**properties)
            apply_category(Categories.SHOP_CAR, item)
            yield item

    def parse_service_centres(self, response):
        for location in response.json()["searchAsaList"]:
            properties = {
                "ref": f"service-{location['asnCd']}",
                "name": location["poiName"],
                "lat": location["displayY"],
                "lon": location["displayX"],
                "addr_full": location["addr"],
                "postcode": location["zip"],
                "phone": location["telNo"],
            }
            item = Feature(**properties)
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
