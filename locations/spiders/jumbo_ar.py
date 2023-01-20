import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class JumboARSpider(scrapy.Spider):
    name = "jumbo_ar"
    item_attributes = {"brand": "Jumbo", "brand_wikidata": "Q6310864"}

    def start_requests(self):
        url = "https://www.jumbo.com.ar/api/dataentities/NT/search?_fields=name,grouping,image_maps,geocoordinates,SellerName,id,country,city,neighborhood,number,postalCode,state,street,schedule,services,paymentMethods,opening,hasPickup,hasDelivery,address,url_image,phone&an=jumboargentina"
        headers = {"Content-Type": "application/json", "Accept": "application/json", "rest-range": "resources=0-999"}

        yield scrapy.Request(url=url, headers=headers, callback=self.parse)

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data)

            (lat, lon) = data["geocoordinates"].split(",")
            item["lat"] = lat
            item["lon"] = lon

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
