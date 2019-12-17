# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem
import json
# import unicodedata


class PrimarkSpider(scrapy.Spider):
    name = "primark"
    brand = "Primark"
    allowed_domains = ["primark.com"]
    start_urls = (
        'https://www.primark.com/en/our-stores',
    )

    def parse_osm(self,opening_table):

        for div in opening_table:
            opening_days = div.xpath('//span[@class="opening-day"]/text()').extract()
            opening_hours = div.xpath('//span[@class="opening-hours text-turquoise"]/text()').extract()
        
        dayhour_list = list(zip(opening_days[:7], opening_hours[:7]))
        dayhour_list.append(dayhour_list.pop(0)) # moving sunday to end of list

        hoursdict = {}
        for dayhour in dayhour_list:
            if dayhour[1] not in hoursdict:
                hoursdict[dayhour[1]] = []

        for dayhour in dayhour_list:
            hoursdict[dayhour[1]].append(dayhour[0])

        osm = ""
        for x in hoursdict:
            if (hoursdict[x][0] == hoursdict[x][-1]):
                osm += hoursdict[x][0] + " " + x + ", "
            else:
                osm += hoursdict[x][0] + "-" + hoursdict[x][-1] + " " + x + ", "
        osm = osm[:-2]

        day_dict = {'Monday':'Mo', 'Tuesday':'Tu', 'Wednesday':'We', 'Thursday':'Th', 'Friday':'Fr', 'Saturday':'Sa', 'Sunday':'Su'}
        pattern = re.compile(r'\b(' + '|'.join(day_dict.keys()) + r')\b')
        osm = pattern.sub(lambda x: day_dict[x.group()], osm.replace(" - ", "-"))

        return osm

    def parse(self, response):
        raw_JSON = re.search(r'showMarks\(\$\.parseJSON\(\'(.*)\'\)\);', response.text)
        dataJSON = json.loads(raw_JSON.group(1))

        for i in range(int(len(dataJSON))):
            link = "https://www.primark.com/en/store/" + dataJSON[i]['Name'].lower().strip().replace(' – ', '-').replace(' - ', '-').replace(' ', '-').replace('\'','').replace('(','').replace(')','').replace(',', '')
            request = scrapy.Request(link, dont_filter=True, callback=self.parse_store, errback=self.handle_fail)
            yield request

    def handle_fail(self,failure):
        pass

    def parse_store(self,response):

        address = (' '.join(response.css('h2.store-address').xpath('text()').extract())).lstrip().rstrip()
        name = ''.join(response.css('div.store-info-text h1.title-level-1').xpath('text()').extract())
        opening_hours = self.parse_osm(response.css('div.opening-times-table div.opening-day-hours'))
        lat, lon = response.xpath('//div[@class="store-location-map"]/a/@href').extract()[0].split('?q=')[1].split(',')
        website = response.url

        postcode = ''
        postmatch = re.search(r'[\d]{5}', address)
        if postmatch:
            postcode = postmatch.group(0)

        phone = ''
        phonematch = response.css('div.phone-number a.title-level-3').xpath('text()')
        if phonematch:
            phone = phonematch.extract()[0].replace("Tel: ","")


        properties = {
            'name': name,
            'addr_full' : address,
            'ref': name,
            'website' : website,
            # 'street': street,
            # 'city': city,
            # 'state' : statezip[:2],
            'postcode' : postcode,
            'opening_hours': opening_hours,
            'phone': phone,
            'lat': lat,
            'lon': lon,
        }

        yield (GeojsonPointItem(**properties))

        
