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
    item_attributes = { 'brand': "Albertsons", 'brand_wikidata': "Q4712282" }
    download_delay = 0.5
    allowed_domains = [
        "local.albertsons.com",
        "local.acmemarkets.com",
        "local.albertsonsmarket.com",
        "local.amigosunited.com",
        "local.andronicos.com",
        "local.carrsqc.com",
        "local.jewelosco.com",
        "local.luckylowprices.com",
        "local.marketstreetunited.com",
        "local.pavilions.com",
        "local.randalls.com",
        "local.shaws.com",
        "local.starmarket.com",
        "local.tomthumb.com",
        "local.unitedsupermarkets.com",
        "local.vons.com"
    ]
    start_urls = (
        'https://local.acmemarkets.com/index.html',
        'https://local.albertsons.com/index.html',
        'https://local.albertsonsmarket.com/index.html',
        'https://local.amigosunited.com/index.html',
        'https://local.andronicos.com/index.html',
        'https://local.carrsqc.com/index.html',
        'https://local.jewelosco.com/index.html',
        'https://local.luckylowprices.com/index.html',
        'https://local.marketstreetunited.com/index.html',
        'https://local.pavilions.com/index.html',
        'https://local.randalls.com/index.html',
        'https://local.shaws.com/index.html',
        'https://local.starmarket.com/index.html',
        'https://local.tomthumb.com/index.html',
        'https://local.unitedsupermarkets.com/index.html',
        'https://local.vons.com/index.html'
    )

    def parse_stores(self, response):
        ref = re.findall(r"[^(\/)]+.html$" ,response.url)
        map_data = response.xpath('normalize-space(//script[@id="js-map-config-dir-map-desktop"]/text())').extract_first()
        map_json= json.loads(map_data)
        if(len(ref)>0):
            ref = ref[0].split('.')[0]
        properties = {
            'addr_full': response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            'phone': response.xpath('normalize-space(//span[@itemprop="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//meta[@itemprop="addressLocality"]/@content)').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'name': response.xpath('normalize-space(//span[@class="LocationName-geo"]/text())').extract_first(),
            'ref': ref,
            'website': response.url,
            'lat':  float(map_json['locs'][0]['latitude']),
            'lon':  float(map_json['locs'][0]['longitude']),
            'brand' : response.xpath('normalize-space(//span[@class="LocationName-brand"]/text())').extract_first()
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
            pattern = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if (pattern.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)

    def parse(self, response):
        urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for path in urls:
            pattern = re.compile("^[a-z]{2}.html$")
            pattern1 = re.compile(r"^[a-z]{2}\/[^()]+\/[^()]+.html$")
            if(pattern.match(path.strip())):
               yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
            elif(pattern1.match(path.strip())):
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
            else:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores)
