import scrapy
from chompjs import chompjs

from locations.categories import Categories, apply_category
from locations.items import Feature

# Official website: https://chizhik.club/


class ChizhikRUSpider(scrapy.Spider):
    name = "chizhik_ru"
    item_attributes = {"brand": "Чижик", "brand_wikidata": "Q124171414"}
    start_urls = [
        "https://yandex.ru/map-widget/v1/?um=constructor:43c5ba1c3f19b99d7a34f4dbfd215a7bfbab6f5f7f165ad3a7050210863923fe&source=constructor"
    ]

    def parse(self, response):
        data = chompjs.parse_js_object(
            response.xpath('//script[@type="application/json" and @class="config-view"]/text()').get()
        )
        for poi in data["userMap"]["features"]:
            item = Feature()
            item["addr_full"] = item["ref"] = poi["title"]
            item["lat"] = poi["coordinates"][1]
            item["lon"] = poi["coordinates"][0]
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
