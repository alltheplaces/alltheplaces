import re

from scrapy import FormRequest, Selector, Spider

from locations.items import Feature
from locations.spiders.starbucks_us import STARBUCKS_SHARED_ATTRIBUTES


class StarbucksTWSpider(Spider):
    name = "starbucks_tw"
    item_attributes = STARBUCKS_SHARED_ATTRIBUTES
    start_urls = ["https://www.starbucks.com.tw/stores/storesearch.jspx"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        yield FormRequest(
            "https://www.starbucks.com.tw/stores/storesearch.jspx",
            formdata={
                "AJAXREQUEST": "j_id_jsp_139507100_0",
                "javax.faces.ViewState": response.xpath('//input[@id="javax.faces.ViewState"]/@value').get(),
                "sbForm:useGeolocation": "0",
                "sbForm:fetchGeolocation": "1",
                "sbForm:lon": "0",
                "sbForm:lat": "0",
                "sbForm:reserve": "",
                "sbForm:pour": "",
                "sbForm:nitro": "",
                "sbForm:drive": "",
                "sbForm:fizzio": "",
                "sbForm:baked": "",
                "sbForm:wifi": "",
                "sbForm:mobileOrder": "",
                "sbForm:mobileOrderInStore": "",
                "sbForm:mobileOrderOutStore": "",
                "sbForm:mobileOrderRoadSide": "",
                "sbForm:coffeeVoucher": "",
                "sbForm:borrowCup": "",
                "sbForm:returnCup": "",
                "sbForm:showUnusualBusinessInfo": "",
                "storeName": "",
                "sbForm_SUBMIT": "1",
                "sbForm:doFindByName": "sbForm:doFindByName",
            },
            callback=self.parse_locations,
        )

    def parse_locations(self, response, **kwargs):
        selector = Selector(text=response.xpath(".").get())
        for location in selector.xpath('//li[@class="store_data"]'):
            item = Feature()
            item["ref"], item["lat"], item["lon"] = re.match(
                r"fetchStoreMapLocation\((\d+),(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\);",
                location.xpath("./@onmouseover").get(),
            ).groups()
            item["name"] = location.xpath('.//*[@class="store_name"]/text()').get()
            item["addr_full"] = location.xpath('.//*[@class="store_add"]/text()').get()
            if details := selector.xpath(f'//div[@id="store_info_{item["ref"]}"]'):
                item["phone"] = details.xpath('.//*[@class="store_phone"]/a/text()').get()
            item["website"] = f'https://www.starbucks.com.tw/stores/storesearch.jspx#store_div_{item["ref"]}'
            yield item
