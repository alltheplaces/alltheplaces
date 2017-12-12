import scrapy
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    'M': 'Mo',
    'T': 'Tu',
    'W': 'We',
    'F': 'Fr',
    'Sat': 'Sa',
    'Sun': 'Su'
}


class DiaryQueenSpider(scrapy.Spider):

    name = "diaryqueen"
    allowed_domains = ["www.dairyqueen.com"]
    download_delay = 0
    start_urls = (
        'http://www.dairyqueen.com/us-en/Sitemap/',
    )

    def parse_day(self, day):

        if re.search('Sat', day) or re.search('Sun', day):
            return DAY_MAPPING[day.strip()]

        if re.search('-', day):
            days = day.split('-')
            osm_days = []
            if len(days) == 2:
                for day in days:
                    osm_day = DAY_MAPPING[day.strip()]
                    osm_days.append(osm_day)
            return "-".join(osm_days)

    def parse_times(self, times):
        if times.strip() == 'Open 24 hours':
            return '24/7'
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
                    hour_min[0] = str(12 + int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        days = lis.xpath('./dt/text()').extract()
        times = lis.xpath('./dd/text()').extract()
        for idx , li in  enumerate(days):
            if li and times[idx]:
                parsed_time = self.parse_times(times[idx])
                parsed_day = li[:2]
                hours.append(parsed_day + ' ' + parsed_time)

        return "; ".join(hours)

    def parse_stores(self, response):
        location_string =re.findall(r"center=[^(&)]+" ,  response.body_as_unicode())
        if(len(location_string)>0):
            lat = float(location_string[0][8:].split(',')[0])
            lng =  float(location_string[0][8:].split(',')[1])
        else:
            lat = ''
            lng = ''
        properties = {
            'addr_full': response.xpath('normalize-space(//hgroup[@itemprop="address"]/h2/text())').extract_first(),
            'phone': response.xpath('normalize-space(//a[@itemprop="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//span[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'ref': re.findall(r"[0-9]+" , response.url)[0],
            'website': response.url,
            'lat': lat,
            'lon': lng,
        }

        hours = self.parse_hours(response.xpath('//dl[@class="store-hours-list"]'))
        if hours:
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)



    def parse(self, response):
        urls = response.xpath('//div[@class="center-960"]/ul/li/a/@href').extract()
        for path in urls:
            yield scrapy.Request(response.urljoin(path), callback=self.parse_stores)
