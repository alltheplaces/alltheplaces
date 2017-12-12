import scrapy
import re
from locations.items import GeojsonPointItem
import json


class LaneBryantSpider(scrapy.Spider):

    name = "lanebryant"
    allowed_domains = ["stores.lanebryant.com"]
    download_delay = 0
    start_urls = (
        'https://stores.lanebryant.com/',
    )

    def parse_stores(self, response):
       data =  response.xpath('normalize-space(//script[@type="application/ld+json"]/text())').extract_first()
       ref = re.findall(r"[^(\/)]+$", response.url)
       if (len(ref) > 0):
            ref = ref[0].split('.')[0]
       try:
         json_data = json.loads(data)
         properties = {
            'addr_full': json_data[0]['address']['streetAddress'] ,
            'phone':json_data[0]['address']['telephone'] ,
            'city': json_data[0]['address']['addressLocality'] ,
            'state': json_data[0]['address']['addressRegion'] ,
            'postcode':json_data[0]['address']['postalCode'] ,
            'ref': ref ,
            'website': response.url,
            'lat': json_data[0]['geo']['latitude'] ,
            'lon':json_data[0]['geo']['longitude'] ,
         }
         properties['opening_hours'] =  json_data[0]['openingHours'],
         yield GeojsonPointItem(**properties)
       except ValueError:
        return


    def parse_city_stores(self, response):
        stores = response.xpath('//div[@id="rls_maplist"]/div/ul/div/div/li/div/a/@href').extract()
        for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@id="rls_maplist"]/div/ul/div/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@id="rls_maplist"]/div/ul/div/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
