import re
import xmltodict

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsVNSpider(Spider):
    name = "mcdonalds_vn"
    item_attributes = McDonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.vn/restaurants.html"]
    no_refs = True


    def parse(self, response):
        raw_data = response.xpath('//script[contains(text(), "function initialize")]').getall()
        for data in raw_data:
            location = xmltodict.parse(data)["script"]
            item = DictParser.parse(location)

            item["name"] = (re.search(r'contentString="(.*?)"', location["#text"])).group(1)
            item["lat"] = (re.search(r'lat:(.*?),', location["#text"])).group(1)
            item["lon"] = (re.search(r'lng:(.*?)}', location["#text"])).group(1)
            
            info = location["div"].get("p")
            for i in info:
                if i["#text"] == 'Address:':
                    item["addr_full"] = i["span"].get("#text")
                if i["#text"] == 'Phone:':
                    item["phone"] = i["span"].get("#text")
                if i["#text"] == 'Email:':
                    item["email"] = i["span"].get("#text")

            apply_category(Categories.FAST_FOOD, item)

            yield item

