import scrapy
import re
import json
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'M': 'Mo',
    'T': 'Tu',
    'W': 'We',
    'F': 'Fr',
    'Sat': 'Sa',
    'Sun': 'Su'
}


class ArgosSpider(scrapy.Spider):

    name = "argos"
    allowed_domains = ["www.argos.co.uk"]
    download_delay = 0
    start_urls = (
        'http://www.argos.co.uk/stores/',
    )
    def parse_stores(self, response):
        data = re.findall(r"window.INITIAL_STATE =[^(<)]+", response.body_as_unicode())
        json_data = json.loads(data[0].replace("window.INITIAL_STATE =" ,''))
        properties = {
            'addr_full':json_data['store']['store']["address"],
            'phone': json_data['store']['store']["tel"],
            'city':json_data['store']['store']["town"],
            'state': '',
            'postcode': json_data['store']['store']["postcode"],
            'ref': json_data['store']['store']["id"],
            'website': response.url,
            'lat': float(json_data['store']['store']["lat"]),
            'lon': float(json_data['store']['store']["lng"]),
        }

        open_hours = ''
        for item in json_data['store']['store']["storeTimes"]:
          open_hours = open_hours + item['date'][ :2]+ ' ' + item['time']+' ;'
        if open_hours:
            properties['opening_hours'] = open_hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//div/div[@class="azsl-panel"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
