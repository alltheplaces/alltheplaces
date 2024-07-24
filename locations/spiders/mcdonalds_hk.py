import scrapy

from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsHKSpider(scrapy.Spider):
    name = "mcdonalds_hk"
    item_attributes = McdonaldsSpider.item_attributes
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://www.mcdonalds.com.hk/wp-admin/admin-ajax.php?action=get_restaurants"
        yield scrapy.http.FormRequest(url=url, formdata={"type": "init"}, method="POST")

    def parse(self, response):
        for index, store in enumerate(response.json()["restaurants"]):
            item = DictParser.parse(store)
            item["website"] = "https://www.mcdonalds.com.hk/"
            item["name"] = "McDonald's " + store["title"]
            item["country"] = "HK"
            item["ref"] = index
            yield item
