import scrapy
import json

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    'Montag': 'Mo',
    'Dienstag': 'Tu',
    'Mittwoch': 'We',
    'MIttwoch': 'We',
    'Donnerstag': 'Th',
    'Donnertag': 'Th',
    'Freitag': 'Fr',
    'Samstag': 'Sa',
    'Sonntag': 'Su'
}

class DennsDeSpider(scrapy.Spider):
    name = "tegut_de"
    allowed_domains = ["www.tegut.com"]
    start_urls = ['https://www.tegut.com/maerkte/marktsuche/seite/1.html?mktegut%5Baddress%5D=Stuttgart&mktegut%5Bradius%5D=200&mktegut%5Bsubmit%5D=Markt%20suchen&cHash=8ab892e19ff6a5ad0c5898779e7dca6f#stores']

    def parse_data(self, response):
        data = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).get()
        data = data.replace('\n', '')
        store = json.loads(data)

        storeid = store.get('@id', None)
        if storeid:
            properties = {
                'ref': storeid,
                'name': store['name'],
                'street': store['address']['streetAddress'],
                'city': store['address']['addressLocality'],
                'postcode': store['address']['postalCode'],
                'country': store['address']['addressCountry'],
                'lat': store['geo']['latitude'],
                'lon': store['geo']['longitude'],
                'phone': store['telephone'],
                'opening_hours': store['openingHours'],
                'extras': {
                    'url': store['url'],
                }
            }

            yield GeojsonPointItem(**properties)

    def parse(self, response):
        stores = response.xpath(
            '//h3[@class="h4 store-title float-left mr-1"]//a/@href'
        ).getall()
        for store in stores:
            yield scrapy.Request(
                f"https://www.tegut.com{store}",
                callback=self.parse_data
            )

        for link in response.xpath('//li[@class="list-inline-item"]//a'):
            next = link.xpath('./text()').get().strip()
            if next == '>':
                print("Next page found")
                next_link = link.xpath('./@href').get()
                print(f"######{next_link}")
                yield scrapy.Request(
                    f"https://www.tegut.com{next_link}",
                    callback=self.parse
                )
