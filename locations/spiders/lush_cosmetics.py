import scrapy
from locations.items import GeojsonPointItem
import json


class LushSpider(scrapy.Spider):
    name = 'lush'
    download_delay = 0
    allowed_domains = ['www.lushusa.com']
    start_urls = [
        'https://www.lushusa.com/on/demandware.store/Sites-Lush-Site/en_US/Stores-Search?lat=41.8781136&lng=-87.62979819999998&radius=50']

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for i in results:
            yield GeojsonPointItem(
                ref=i['storeInfo']['id'],
                name=i['storeInfo']['name'],
                phone=i['storeInfo']['phone'],
                street=i['storeInfo']['address1'],
                postcode=i['storeInfo']['postalCode'],
                city=i['storeInfo']['city'],
                state=i['storeInfo']['state'],
                lat=i['storeInfo']['lat'],
                lon=i['storeInfo']['lng'],
                addr_full=f"{i['storeInfo']['address1']}"
                          f" {i['storeInfo']['city']}, "
                          f"{i['storeInfo']['state']} "
                          f"{i['storeInfo']['postalCode']}"
            )
