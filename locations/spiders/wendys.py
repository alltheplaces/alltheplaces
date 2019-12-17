import scrapy
import re
import json
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'Monday': 'Mo',
    'Tuesday': 'Tu',
    'Wednesday': 'We',
    'Thursday': 'Th',
    'Friday': 'Fr',
    'Saturday': 'Sa',
    'Sunday': 'Su'
}


class WendysSpider(scrapy.Spider):

    name = "wendys"
    chain_name = "Wendy's"
    allowed_domains = ["locations.wendys.com"]
    download_delay = 0.5
    download_timeout = 30
    start_urls = (
        'https://locations.wendys.com',
    )

    def handle_error(self, failure):
        self.log("Request failed: %s" % failure.request)
    def parse_day(self, day):
            return DAY_MAPPING[day.strip()]
    def parse_times(self, times):
        hours_to = [x.strip() for x in times.split('-')]
        cleaned_times = []

        for hour in hours_to:
            if re.search('pm$', hour):
                hour = re.sub('pm', '', hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search('am$', hour):
                hour = re.sub('am', '', hour).strip()
                hour_min = hour.split(":")
                if len(hour_min[0]) <2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str(int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath('./span[@class="day"]/text()').extract()[1]
            times = li.xpath('./span[2]/text()').extract_first()
            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + ' ' + parsed_time)

        return "; ".join(hours)
    def parse_stores(self, response):
        page_content = response.body_as_unicode()
        json_content = re.findall('li.data.results =[^;]+' , page_content)
        if len(json_content)>0:
            json_content =  json_content[0].replace('li.data.results =' ,'')
        json_data =  json.loads(json_content)
        properties = {
            'addr_full': json_data[0]['address'],
            'phone':json_data[0]['phone'],
            'city': json_data[0]['city'],
            'state':json_data[0]['state'],
            'postcode': json_data[0]['postal'],
            'ref': json_data[0]['id'],
            'website': response.url,
            'lat': json_data[0]['lat'],
            'lon': json_data[0]['lon'],
        }
        hours = self.parse_hours(response.xpath('//div[@class="hours"]/ol/li'))
        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath('//div[@class="col-xs-12 col-lg-10 col-lg-offset-1"]/article/ul/li/a/@href').extract()
        for store in stores:
            if store:
                yield scrapy.Request(response.urljoin(store), callback=self.parse_stores ,errback=self.handle_error)

    def parse_state(self, response):
        city_urls = response.xpath('//div[@class="col-xs-12 col-lg-10 col-lg-offset-1"]/article/div[@class="col"]/ul/li/a/@href').extract()
        for path in city_urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_city_stores ,errback=self.handle_error)

    def parse(self, response):
        urls = response.xpath('//div[@class="col-xs-12 col-lg-10 col-lg-offset-1"]/article/div[@class="col"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_state ,errback=self.handle_error)
