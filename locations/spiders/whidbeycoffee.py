import scrapy
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su"
}


class WhidbeycoffeeSpider(scrapy.Spider):

    name = "whidbeycoffee"
    brand = "Whidbey Coffee"
    allowed_domains = ["www.whidbeycoffee.com"]
    download_delay = 1
    start_urls = (
        'http://www.whidbeycoffee.com/pages/locations',
    )

    def parse_day(self, day):
        if re.search('-', day):
            days = day.split('-')
            osm_days = []
            if len(days) == 2:
                for day in days:
                    try:
                        osm_day = DAY_MAPPING[day.strip()]
                        osm_days.append(osm_day)
                    except:
                        return None
            return ["-".join(osm_days)]
        if re.search('Sat', day) or re.search('Sun', day):
            if re.search('Sat', day) and re.search('Sun', day):
                return ['Sa', 'Su']
            else:
                return [DAY_MAPPING[day.strip()]]

    def parse_times(self, times):
        if times.strip() == 'Closed':
            return 'off'
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
        for li in lis:
            li = li.lstrip()
            if re.search('&', li):
                day = li.split(':')[0]
            else:
                day = re.findall(r"^[^( |:)]+" ,li)[0]
            times = li.replace(day , "")[1:]

            if times and day:
                parsed_time = self.parse_times(times)
                parsed_day = self.parse_day(day)
                if parsed_day is not None:
                    if (len(parsed_day) == 2):
                        hours.append(parsed_day[0] + ' ' + parsed_time)
                        hours.append(parsed_day[1] + ' ' + parsed_time)
                    else:
                        hours.append(parsed_day[0] + ' ' + parsed_time)

        return "; ".join(hours)

    def parse(self, response):
        stores = response.xpath('//h5')
        for index , store in enumerate(stores):
            direction_link = store.xpath('normalize-space(./following-sibling::p/a/@href)').extract_first()
            properties = {
                'addr_full': store.xpath('./following-sibling::p/a/text()').extract()[0],
                'phone': store.xpath('./following-sibling::p/following-sibling::p/text()').extract()[0],
                'city': store.xpath('./following-sibling::p/a/text()').extract()[1].split(',')[0],
                'state':  store.xpath('./following-sibling::p/a/text()').extract()[1].split(',')[1].split(' ')[1],
                'postcode':  store.xpath('./following-sibling::p/a/text()').extract()[1].split(',')[1].split(' ')[2],
                'ref':store.xpath('normalize-space(./text())').extract_first(),
                'lat':re.findall(r"\/@[^(\/)]+", direction_link)[0].split(',')[0][2:],
                'lon': re.findall(r"\/@[^(\/)]+", direction_link)[0].split(',')[1],
            }
            if(index==0):
                hours = self.parse_hours(store.xpath('./following-sibling::p[3]/text()').extract())
            else:
                hours = self.parse_hours(store.xpath('./following-sibling::p[2]/text()').extract()[2:])

                if hours:
                    properties['opening_hours'] = hours

                yield GeojsonPointItem(**properties)
