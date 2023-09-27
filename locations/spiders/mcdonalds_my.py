import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsMYSpider(scrapy.Spider):
    name = "mcdonalds_my"
    item_attributes = McDonaldsSpider.item_attributes

    def start_requests(self):
        form_data = {
            "action": "get_nearby_stores",
            "distance": "100000",
            "lat": "4",
            "lng": "101",
            "ajax": "1",
        }
        yield scrapy.http.FormRequest(
            url="https://www.mcdonalds.com.my/storefinder/index.php",
            method="POST",
            formdata=form_data,
            callback=self.parse,
        )

    def parse(self, response):
        for index, store in enumerate(response.json()["stores"]):
            item = DictParser.parse(store)
            item["website"] = "https://www.mcdonalds.com.my"
            item["ref"] = index
            apply_category(Categories.FAST_FOOD, item)
            yield item
