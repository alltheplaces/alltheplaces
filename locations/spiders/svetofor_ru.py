import scrapy
from chompjs import chompjs

from locations.categories import Categories, apply_category
from locations.items import Feature


class SvetoforRUSpider(scrapy.Spider):
    name = "svetofor_ru"
    item_attributes = {"brand_wikidata": "Q61875920"}
    start_urls = ["https://svetoforonline.ru/shops/"]

    def parse(self, response):
        data = response.xpath('//script[@type="text/javascript" and contains(text(), "var myPlacemark")]').get()
        for line in data.split(";"):
            if line.startswith("var myPlacemark"):
                poi = chompjs.parse_js_objects(line)
                item = Feature()
                for attribute in poi:
                    if isinstance(attribute, list):
                        item["lat"], item["lon"] = attribute
                    elif isinstance(attribute, dict) and attribute.get("balloonContent"):
                        balloon = attribute["balloonContent"]
                        item["addr_full"] = balloon.split("<br />")[0]
                        item["ref"] = item["website"] = "https:" + scrapy.Selector(text=balloon).xpath("//a/@href").get(
                            default=""
                        )
                apply_category(Categories.SHOP_SUPERMARKET, item)
                yield item
