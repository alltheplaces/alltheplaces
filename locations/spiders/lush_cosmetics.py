import scrapy
from locations.items import GeojsonPointItem
import json


class LushSpider(scrapy.Spider):
    name = 'lush'
    download_delay = 0
    allowed_domains = ['www.lushusa.com']
    start_urls = [
        'https://www.lushusa.com/on/demandware.store/Sites-Lush-Site/default/Stores-FindStores?showMap=false&radius=50000&postalCode=78704'
    ]

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for i in results["stores"]:
            yield GeojsonPointItem(
                ref=i['ID'],
                name=i['name'],
                phone=i.get('phone'),
                addr_full=i['address1'],
                postcode=i['postalCode'],
                city=i['city'],
                state=i['stateCode'],
                country=i['countryCode'],
                lat=i['latitude'],
                lon=i['longitude'],
            )
