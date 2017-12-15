import scrapy
import re
import json
from locations.items import GeojsonPointItem
class ArgosSpider(scrapy.Spider):

    name = "boots"
    allowed_domains = ["www.boots.com"]
    download_delay = 0.5
    start_urls = (
        'http://www.boots.com/store-a-z',
    )
    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath('normalize-space(./td[@class="store_hours_day"]/text())').extract_first()
            times = li.xpath('normalize-space(./td[@class="store_hours_time"]/text())').extract_first()
            if times and day:
                hours.append(day[:2] + ' ' + times)

        return "; ".join(hours)

    def parse_stores(self, response):
        addr_full = response.xpath('//section[@class="store_details_content rowContainer"]/dl[@class="store_info_list"][1]/dd[@class="store_info_list_item"]/text()').extract()
        if(len(addr_full)<3):
            return
        properties = {
            'addr_full':addr_full[0],
            'phone': response.xpath('//section[@class="store_details_content rowContainer"]/dl[@class="store_info_list"][3]/dd[@class="store_info_list_item"]/a/text()').extract_first(),
            'city':addr_full[1],
            'state': addr_full[2],
            'postcode':addr_full[3],
            'country': 'United Kingdom',
            'ref': response.xpath('normalize-space(//input[@id="storeId"]/@value)').extract_first(),
            'website': response.url,
            'lat': float(response.xpath('normalize-space(//input[@id="lat"]/@value)').extract_first()),
            'lon': float(response.xpath('normalize-space(//input[@id="lon"]/@value)').extract_first()),
        }
        hours = self.parse_hours(response.xpath('//div[@class="row store_all_opening_hours"]/div[1]/table[@class="store_opening_hours "]/tbody/tr'))
        if hours:
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//div[@class="brand_list_viewer"]/div[@class="column"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)