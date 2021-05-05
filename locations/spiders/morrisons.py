import scrapy
import re
import json
from locations.items import GeojsonPointItem

DAYS = {
    'mon': 'Mo',
    'tue': 'Tu',
    'wed': 'We',
    'fri': 'Fr',
    'thu': 'Th',
    'sat': 'Sa',
    'sun': 'Su',
}


class MorrisonsSpider(scrapy.Spider):

    name = "morrisons"
    item_attributes = {'brand': "Morrisons"}
    allowed_domains = ["my.morrisons.com", "api.morrisons.com"]
    download_delay = 0.5
    start_urls = (
        'https://my.morrisons.com/storefinder/list/a',
    )

    def store_hours(self, store_hours):
        clean_time = ''
        for key, value in store_hours.items():
            if ('open' in value and 'close' in value):
                if re.search('[0-9]{2}:[0-9]{2}:[0-9]{2}', value['open']) and re.search('[0-9]{2}:[0-9]{2}:[0-9]{2}', value['close']):
                    clean_time = clean_time + DAYS[key] + ' ' + value['open'][0:5] + '-' + \
                                 value['close'][0:5] + ';'
                else:
                    clean_time = clean_time + DAYS[key] + ' ' + 'Closed' + ';'

        return clean_time

    def parse_stores(self, response):
        data = json.loads(response.body_as_unicode())
        address = data['address']['addressLine1']+" "+data['address']['addressLine2'].replace("None", "")
        properties = {
            'addr_full': address.strip(),
            'phone':data['telephone'],
            'city': data['address']['city'],
            'state': '',
            'postcode': data['address']['postcode'],
            'ref': data['name'],
            'name': data['storeName'],
            'country':data['address']['country'],
            'website': 'https://my.morrisons.com/storefinder/'+str(data['name']),
            'lat': data['location']['latitude'],
            'lon':  data['location']['longitude'],
        }

        hours = self.store_hours(data['openingTimes'])
        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse_alpha(self, response):
        alpha_urls = response.xpath('//div[@class="col-md-4 col-sm-6"]/a/@href').extract()
        for path in alpha_urls:
            id = re.findall(r"[0-9]+$" , path)[0]
            url = 'https://api.morrisons.com/location/v2//stores/%s?apikey=kxBdM2chFwZjNvG2PwnSn3sj6C53dLEY&include=departments,services,linkedStores'%(id)
            yield scrapy.Request(response.urljoin(url), callback=self.parse_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="azWrapper"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_alpha)
