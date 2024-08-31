from chompjs import parse_js_object
from scrapy import Selector, Spider

from locations.dict_parser import DictParser


class OkFurnitureSpider(Spider):
    name = "ok_furniture"
    item_attributes = {"brand": "OK Furniture", "brand_wikidata": "Q116474866"}
    allowed_domains = ["okfurniture.co.za"]
    start_urls = ["https://www.okfurniture.co.za/store-locator/"]
    skip_auto_cc_domain = True

    def parse(self, response):
        js_blob = [
            i
            for i in response.xpath('//script[contains(text(),"var markers1 = [{")]').get().split("\n")
            if i.strip().startswith("var markers1 = [{")
        ][0]
        json_blob = parse_js_object(js_blob, json_params={"strict": False})

        for location in json_blob:
            item = DictParser.parse(location)
            item["ref"] = location["storelocatorid"]
            item["branch"] = item.pop("name")
            item["addr_full"] = item["addr_full"].replace("</br>", "")
            try:
                item["phone"] = Selector(text=location["contact"]).xpath("//a/@href").get().replace("tel:", "")
                if not (item["phone"].startswith("0") or item["phone"].startswith("(")):
                    item["phone"] = "0" + item["phone"]
            except:
                pass

            yield item
