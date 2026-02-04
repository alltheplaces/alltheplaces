import re

from scrapy import FormRequest, Selector, Spider

from locations.items import Feature


class StarbucksTWSpider(Spider):
    name = "starbucks_tw"
    item_attributes = {"brand": "星巴克", "brand_wikidata": "Q37158"}
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self):
        yield FormRequest(
            "https://www.starbucks.com.tw/stores/ajax/json_storesearch.aspx",
            formdata={
                "lat": "0",
                "lon": "0",
            },
            callback=self.parse,
        )

    def parse(self, response, **kwargs):
        selector = Selector(text=response.json()["renderElements"][0]["elementHTML"])
        for location in selector.xpath('//li[@class="store_data"]'):
            item = Feature()
            item["ref"], item["lat"], item["lon"] = re.match(
                r"fetchStoreMapLocation\((\d+)\s*,\s*(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\)",
                location.xpath("./@onmouseover").get(""),
            ).groups()
            item["branch"] = location.xpath('.//*[@class="store_name"]/text()').get()
            item["addr_full"] = location.xpath('.//*[@class="store_add"]/text()').get()
            if details := selector.xpath(f'//div[@id="store_info_{item["ref"]}"]'):
                item["phone"] = details.xpath('.//*[@class="store_phone"]/a/text()').get()
            item["website"] = f'https://www.starbucks.com.tw/stores/storesearch.jspx#store_div_{item["ref"]}'
            yield item
