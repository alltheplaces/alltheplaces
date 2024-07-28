import ast

from scrapy import Selector
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES


class AviaRSSpider(Spider):
    name = "avia_rs"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    start_urls = [
        "https://radunavia.rs/en/avia-petrol-stations",
    ]
    no_refs = True

    def parse(self, response, **kwargs):
        data = ast.literal_eval(
            response.xpath('//script[contains(text(), "var markers")]').re_first(r"infoWindowContent=(\[.*\]);")
        )
        lat_lon_data = ast.literal_eval(
            response.xpath('//script[contains(text(), "var markers")]').re_first(
                r"var markers=(\[.*\]);var infoWindowContent"
            )
        )
        for station in data:
            item = Feature()
            address_data = Selector(text=station[0])
            item["name"] = address_data.xpath(r"//h5/text()").get()
            item["addr_full"] = address_data.xpath(r"//p/text()").get()
            item["phone"] = address_data.xpath(r"//p[3]/text()").get()
            item["website"] = "https://radunavia.rs/"
            for lat_lon in lat_lon_data:
                if item["name"] in lat_lon:
                    item["lat"] = lat_lon[1]
                    item["lon"] = lat_lon[2]
            apply_category(Categories.FUEL_STATION, item)

            yield item
