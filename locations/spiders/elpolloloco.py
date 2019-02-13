import scrapy
import re
from locations.items import GeojsonPointItem

class ElPolloLocoSpider(scrapy.Spider):
    name = "elpolloloco"
    allowed_domains = ["www.elpolloloco.com"]
    start_urls = (
        'https://www.elpolloloco.com/locations/all-locations.html',
    )

    def parse_stores(self, response):
        properties = {
            'addr_full': response.xpath('normalize-space(//meta[@itemprop="streetAddress"]/@content)').extract_first(),
            'phone': response.xpath('normalize-space(//div[@itemprop="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//meta[@itemprop="addressLocality"]/@content)').extract_first(),
            'state': response.xpath('normalize-space(//meta[@itemprop="addressRegion"]/@content)').extract_first(),
            'postcode':response.xpath('normalize-space(//meta[@itemprop="postalCode"]/@content)').extract_first(),
            'ref': response.xpath('normalize-space(//div[@itemprop="branchCode"]/text())').extract_first(),
            'website': response.url,
            'lat': response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first(),
            'lon': response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first(),
            'opening_hours': self.parse_opening_hours(response.xpath('//div[@itemprop="openingHoursSpecification"]')),
        }
        yield GeojsonPointItem(**properties)

    def parse_opening_hours(self, opening_hours_div):
        result_array = []
        for div in opening_hours_div:
            day_of_week_list = div.xpath('normalize-space(./meta[@itemprop="dayOfWeek"]/@href)').extract_first().rsplit("/",1)
            open_time = div.xpath('normalize-space(./meta[@itemprop="opens"]/@content)').extract_first().rsplit(":",1)[0]
            close_time = div.xpath('normalize-space(./meta[@itemprop="closes"]/@content)').extract_first().rsplit(":",1)[0]
            
            if (len(day_of_week_list) == 2):
                day_of_week = day_of_week_list[-1][:2]
                result_array.append("%s %s-%s" % (day_of_week, open_time, close_time))
        return ';'.join(result_array)



    def parse(self, response):
        urls = response.xpath('//p[@class="locaFLstoreInfo" and ./a/span[@class ="locaSSComingSoon" and not(contains(./text(),"(Coming Soon)"))]]/a/@href').extract()
        for path in urls:
                yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
