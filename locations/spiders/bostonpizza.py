# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours



class BostonPizzaSpider(scrapy.Spider):
    name = "bostonpizza"
    item_attributes = {"brand": "Boston Pizza"}
    allowed_domains = ["www.bostonpizza.com"]
    start_urls = ("https://bostonpizza.com/content/bostonpizza/en/locations/jcr:content/root/container_73434033/map.getAllRestaurants.json",)


    def parse(self, response):
        data = json.loads(json.dumps(response.json()))
        for i in data['map']['response']:
            properties = {
                "ref": i["identifier"],
                "name": i["restaurantName"],
                "addr_full": i["address"],
                "city": i["city"],
                "state": i["province"],
                "postcode": i["postalCode"],
                "country": i["country"],
                "phone": i["restaurantPhoneNumber"],
                "lat": i["latitude"],
                "lon": i["longitude"],
            }

            yield GeojsonPointItem(**properties)
