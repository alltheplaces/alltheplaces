import scrapy
import re
from locations.items import GeojsonPointItem

DAYS={
    'monday':'Mo',
    'tuesday':'Tu',
    'wednesday':'We',
    'friday':'Fr',
    'thursday':'Th',
    'saturday':'Sa',
    'sunday':'Su',
}

class GNCSpider(scrapy.Spider):

    name = "gnc"
    allowed_domains = ["stores.gnc.com"]
    download_delay = 0.5
    start_urls = (
        'http://stores.gnc.com/',
    )

    def parse_stores(self, response):
        properties = {
            'addr_full': response.xpath('normalize-space(//meta[@property="business:contact_data:street_address"]/@content)').extract_first(),
            'phone' : response.xpath('normalize-space(//meta[@property="business:contact_data:phone_number"]/@content)').extract_first(),
            'city' : response.xpath('normalize-space(//meta[@property="business:contact_data:locality"]/@content)').extract_first(),
            'state': response.xpath('normalize-space(//meta[@property="business:contact_data:region"]/@content)').extract_first(),
            'postcode': response.xpath('normalize-space(//meta[@property="business:contact_data:postal_code"]/@content)').extract_first(),
            'ref' : re.findall(r"[^(\/)]+$", response.url)[0] ,
            'website' : response.url,
            'lat' : response.xpath('normalize-space(//meta[@property="place:location:latitude"]/@content)').extract_first(),
            'lon' : response.xpath('normalize-space(//meta[@property="place:location:longitude"]/@content)').extract_first(),
        }

        days= response.xpath('//meta[@property="business:hours:day"]/@content').extract()
        starts = response.xpath('//meta[@property="business:hours:start"]/@content').extract()
        ends = response.xpath('//meta[@property="business:hours:end"]/@content').extract()
        hours = ''
        for idx , day in enumerate(days):
            hours =  hours+DAYS[day.strip()]+' '+starts[idx][:5]+'-'+ends[idx][:5]+' ;'
        if hours:
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@id="pl-result-list"]/div/h2/a/@href').extract()
        if(len(stores)==0):
            return
        else:
            for store in stores:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores)
        page = response.meta['page']+1
        yield  scrapy.Request(response.urljoin(response.meta['url']+'?page='+str(page)), callback=self.parse_city_stores ,meta={'page':page,'url':response.meta['url']})

    def parse_state(self, response):
        city_urls = response.xpath('//div[@id="pl-state-list-container"]/article/div/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores ,meta={'page':1 ,'url':response.urljoin(path)})
    def parse(self, response):
        urls = response.xpath('//div[@id="pl-state-list"]/article/div/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state)
