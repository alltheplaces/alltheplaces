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


class AlbertsonsSpider(scrapy.Spider):

    name = "albertsons"
    download_delay = 0.5
    allowed_domains = [
        "local.albertsons.com",
        "local.jewelosco.com",
    ]
    start_urls = (
        'https://local.albertsons.com/index.html',
        'https://local.jewelosco.com/index.html',
    )

    def parse_stores(self, response):
        ref = re.findall(r"[^(\/)]+.html$" ,response.url)
        map_data = response.xpath('normalize-space(//script[@id="js-map-config-dir-map-desktop"]/text())').extract_first()
        map_json= json.loads(map_data)
        if(len(ref)>0):
            ref = ref[0].split('.')[0]
        properties = {
            'addr_full': response.xpath('normalize-space(//span[@itemprop="streetAddress"]/span/text())').extract_first(),
            'phone': response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': ref,
            'website': response.url,
            'lat':  float(map_json['locs'][0]['latitude']),
            'lon':  float(map_json['locs'][0]['longitude']),
        }
        hours = response.xpath('//div[@class="LocationInfo-right"]/div[1]/div[@class="LocationInfo-hoursTable"]/div[@class="c-location-hours-details-wrapper js-location-hours"]/table/tbody/tr/@content').extract()
        if hours:
            properties['opening_hours'] = "; ".join(hours)
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self ,response):
        stores = response.xpath('//div[@class="Teaser-content"]/h2/a/@href').extract()
        for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)

    def parse_state(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if (pattern.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}.html$")
            pattern1 = re.compile("^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if(pattern.match(path.strip())):
               yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif(pattern1.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
