import scrapy
import re
from locations.items import GeojsonPointItem

class GucciSpider(scrapy.Spider):

    name = "gucci"
    allowed_domains = ["www.gucci.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.gucci.com/us/en/store',
    )

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
            day = li.xpath('normalize-space(./td[@class="store-detail-store-hours-day"]/text())').extract_first()
            times = li.xpath('normalize-space(./td[@class="store-detail-store-hours-hour"]/span/text())').extract_first()
            if times and day:
                parsed_time = self.parse_times(times)
                hours.append(day.strip()[:2] + ' ' + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        location =  re.findall(r"=[0-9.-]+" ,response.url)
        properties = {
            'addr_full': response.xpath('normalize-space(//div[@itemprop="streetAddress"]/text())').extract_first(),
            'phone': response.xpath('normalize-space(//a[@itemprop="telephone"]/text())').extract_first().replace('T:',''),
            'city': '',
            'state':  response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first().replace(',',''),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': response.xpath('normalize-space(//div[@itemprop="streetAddress"]/text())').extract_first().replace(' ' ,'-'),
            'website': response.url,
            'lat': float(location[0][1:]),
            'lon': float(location[1][1:]),
        }
        hours = self.parse_hours(response.xpath('//tr[@class="store-detail-store-hours-table-row"]'))
        if hours:
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//h3[@class="name"]/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
