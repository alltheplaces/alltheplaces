from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FoodworksAUSpider(Spider):
    name = "foodworks_au"
    item_attributes = {"brand": "Foodworks", "brand_wikidata": "Q5465579"}
    start_urls = ["https://chooser.myfoodworks.com.au/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@class="StoreCard StoreCard--WithStoreAttributes"]'):
            item = Feature()
            item["branch"] = store.xpath('.//*[@class="StoreCard__Name"]/text()').get()
            item["street_address"] = store.xpath('.//*[@class="StoreCard__Details"]//text()[3]').get()
            item["addr_full"] = merge_address_lines(
                [item["street_address"], store.xpath('.//*[@class="StoreCard__Details"]//text()[4]').get()]
            )
            if phone := store.xpath('.//*[contains(@href,"tel:")]/@href').get():
                item["phone"] = phone.replace("tel:", "")
            item["ref"] = store.xpath('.//*[contains(@href,"i_choose_you")]/@href').get().replace("catalogues", "")
            if website := store.xpath('.//*[contains(@href,"catalogues")]/@href').get():
                item["website"] = website.replace("catalogues", "")
            yield item
