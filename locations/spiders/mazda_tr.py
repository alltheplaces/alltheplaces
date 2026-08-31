from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.mazda_jp import MAZDA_SHARED_ATTRIBUTES


class MazdaTRSpider(Spider):
    name = "mazda_tr"
    item_attributes = MAZDA_SHARED_ATTRIBUTES
    start_urls = ["https://www.mazda.com.tr/tr/yetkili-servis-bul.html"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="pb-5 text-center menu-bosluk"]/div/div[2]/div'):
            item = Feature()
            item["name"] = location.xpath(".//p[1]//text()").get()
            item["city"] = location.xpath(".//p[2]//text()").get()
            item["phone"] = location.xpath(".//p[3]//text()").get()
            apply_category(Categories.SHOP_CAR_REPAIR, item)
            yield item
