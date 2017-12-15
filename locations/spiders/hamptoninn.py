# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem


class HamptonInnSpider(scrapy.Spider):
    name = "hamptoninn"
    allowed_domains = ['hamptoninn3.hilton.com']
    start_urls = (
        'http://hamptoninn3.hilton.com/sitemapurl-hp-00000.xml',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        regex = re.compile(r'http(://|ps://)(www.|)hamptoninn\d.hilton.com/en/hotels/\w+/\S+/maps-directions/index.html')
        for path in city_urls:
            if re.search(regex,path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):

        json_data = response.xpath('//div/script[@type="application/ld+json"]/text()').extract_first().replace('\n','').replace('\r','').replace('\t','')
        json_data = json_data.replace('\\','').replace(": '", ': "').replace("',",'",').replace("'}",'"}').replace(',}','}')
        json_data = json_data.replace('// if the location file does not have the hours separated into open/close for each day, remove the below section', '')
        data = json.loads(json_data)

        regex = re.compile(r'http(://|ps://)(www.|)hamptoninn\d.hilton.com/en/hotels/\w+/\S+/maps-directions/index.html')
        if re.search(regex,response.request.url):
            properties = {
            'name': data['name'],
            'ref': data['name'],
            'addr_full': data['address']['streetAddress'],
            'city': data['address']['addressLocality'],
            'state': data['address']['addressRegion'],
            'postcode': data['address']['postalCode'],
            'phone': data['telephone'],
            'website': response.request.url,
            'opening_hours': data['openingHours'],
            'lat': float(data['geo']['latitude']),
            'lon': float(data['geo']['longitude']),
            }

            open('/tmp/json.txt', 'w').write(str(properties))

            yield GeojsonPointItem(**properties)

        else:
            pass