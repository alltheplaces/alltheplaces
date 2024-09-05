from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class DiscoArgentinaSpider(Spider):
    name = "disco_argentina"
    item_attributes = {"brand": "Supermercados Disco", "brand_wikidata": "Q6135978"}
    allowed_domains = ["www.disco.com.ar"]
    start_urls = [
        "https://www.disco.com.ar/api/dataentities/NT/search?_fields=name,grouping,image_maps,geocoordinates,SellerName,id,country,city,neighborhood,number,postalCode,state,street,schedule,services,paymentMethods,opening,hasPickup,hasDelivery,address,url_image,phone"
    ]
    user_agent = BROWSER_DEFAULT

    def start_requests(self):
        yield Request(url=self.start_urls[0], headers={"Accept": "application/json", "Rest-Range": "resources=0-999"})

    def parse(self, response):
        shops = response.json()
        for shop in shops:
            item = DictParser.parse(shop)
            item["lat"] = shop["geocoordinates"].split(",")[0]
            item["lon"] = shop["geocoordinates"].split(",")[1]
            yield item
