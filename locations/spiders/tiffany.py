import scrapy
import re
import json
from locations.items import GeojsonPointItem

class TiffanySpider(scrapy.Spider):

    name = "tiffany"
    item_attributes = { 'brand': "Tiffany" }
    allowed_domains = ["www.tiffany.com"]
    download_delay = 0.5
    start_urls = (
        'http://www.tiffany.com/jewelry-stores/store-list/united-states',
    )

    def parse_day(self, day):
        if re.search('-', day):
            days = day.split('-')
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = day.strip()[:2]
                    osm_days.append(osm_day)
            return "-".join(osm_days)
        return day.strip()[:2]

    def parse_times(self, times):
        if times.strip() == 'CLOSED':
            return 'Closed'
        hours_to = [x.strip() for x in times.split('-')]
        cleaned_times = []
        for hour in hours_to:
            if re.search('PM$', hour):
                hour = re.sub('PM', '', hour).strip()
                hour_min = hour.split(":")
                if int(hour_min[0]) < 12:
                    hour_min[0] = str(12 + int(hour_min[0]))
                cleaned_times.append(":".join(hour_min))

            if re.search('AM$', hour):
                hour = re.sub('AM', '', hour).strip()
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
          if re.search(r"([0-9]{1,2}):([0-9]{1,2})([APM]{2})|CLOSED" , li):
            day = li.split(':')[0]
            times = li.replace(day+':','')
            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + ' ' + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        properties = {
            'addr_full': data['address']['streetAddress'],
            'phone': data['telephone'],
            'name': data['name'],
            'city': data['address']['addressLocality'],
            'state': data['address']['addressRegion'],
            'postcode': data['address']['postalCode'],
            'ref': data['name'].replace(' ','_'),
            'website': response.url,
            'lat': float(data['geo']['latitude']),
            'lon': float(data['geo']['longitude']),
        }

        hours = self.parse_hours(response.xpath('//div[@id="divExtendedInfo"]/text()').extract())
        if hours:
            properties['opening_hours'] = hours
        yield GeojsonPointItem(**properties)

    def parse(self, response):
        urls = response.xpath('//a[contains(text(),"View on Map")]/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
