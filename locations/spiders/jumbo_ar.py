import scrapy

from locations.categories import apply_category, Categories
from locations.dict_parser import DictParser


class JumboARSpider(scrapy.Spider):
    name = "jumbo_argentina"
    item_attributes = {"brand": "Jumbo"}
    allowed_domains = ["www.jumbo.com.ar"]

    def start_requests(self):
        url = "https://www.jumbo.com.ar/api/dataentities/NT/search?_fields=name,grouping,image_maps,geocoordinates,SellerName,id,country,city,neighborhood,number,postalCode,state,street,schedule,services,paymentMethods,opening,hasPickup,hasDelivery,address,url_image,phone&an=jumboargentina"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "rest-range": "resources=0-999"
        }

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)

            (lat, lon) = data["geocoordinates"].split(',')
            item["lat"] = lat
            item["lon"] = lon

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
