import re

import chompjs
from scrapy import Selector, Spider

from locations.items import Feature
from locations.spiders.burger_king import BurgerKingSpider


class BurgerKingMXSpider(Spider):
    name = "burger_king_mx"
    item_attributes = BurgerKingSpider.item_attributes
    start_urls = ["https://www.burgerking.com.mx/es/restaurantes/index-s.html"]
    no_refs = True

    def parse(self, response, **kwargs):
        data = response.xpath('//script[contains(., "const features")]/text()').get()
        if m := re.search(r"const features = (\[.+\]);", data, re.DOTALL):
            for location in chompjs.parse_js_object(m.group(1)):
                item = Feature()
                item["name"] = location["title"]
                if ll := re.search(r"LatLng\((-?\d+\.\d+),(-?\d+\.\d+)\)", location["position"]):
                    item["lat"], item["lon"] = ll.groups()

                sel = Selector(text=location["description"])
                item["website"] = sel.xpath("//@href").get()  # URL for town, not POI
                item["addr_full"] = sel.xpath("//h4/text()").get()

                yield item
