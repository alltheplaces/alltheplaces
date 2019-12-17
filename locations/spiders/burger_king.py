import scrapy
import re
from locations.items import GeojsonPointItem

day_formats = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su"
}


class BurgerKingSpider(scrapy.Spider):
    name = "burgerking"
    item_attributes = { 'brand': "Burger King" }
    allowed_domains = ["locations.bk.com"]
    download_delay = 0.2
    start_urls = (
        'https://locations.bk.com/index.html',
    )

    def parse_day(self, day):

        return day_formats[day.strip()]

    def parse_times(self, times):

        if times.strip() == 'Open 24 hours':
            return '24/7'
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
                if len(hour_min[0]) < 2:
                    hour_min[0] = hour_min[0].zfill(2)
                else:
                    hour_min[0] = str(12 + int(hour_min[0]))

                cleaned_times.append(":".join(hour_min))
        return "-".join(cleaned_times)

    def parse_hours(self, lis):
        hours = []
        for li in lis:
            day = li.xpath('normalize-space(.//td[@class="c-location-hours-details-row-day"]/text())').extract_first()
            times = li.xpath('.//td[@class="c-location-hours-details-row-intervals"]/span/span/text()').extract()
            times_all = "".join(str(x) for x in times)
            if times_all and day:
                parsed_time = self.parse_times(times_all)
                parsed_day = self.parse_day(day)
                hours.append(parsed_day + ' ' + parsed_time)

        return "; ".join(hours)

    def parse_store(self, response):
        properties = {
            'addr_full': response.xpath('normalize-space(//div[@class="c-AddressRow"]/span[@class="c-address-street-1"]/text())').extract_first(),
            'phone': response.xpath('normalize-space(//span[@id="telephone"]/text())').extract_first(),
            'city': response.xpath('normalize-space(//span[@itemprop="addressLocality"]/text())').extract_first(),
            'state': response.xpath('normalize-space(//abbr[@itemprop="addressRegion"]/text())').extract_first(),
            'postcode': response.xpath('normalize-space(//span[@itemprop="postalCode"]/text())').extract_first(),
            'lat': float(response.xpath('normalize-space(//meta[@itemprop="latitude"]/@content)').extract_first()),
            'lon': float(response.xpath('normalize-space(//meta[@itemprop="longitude"]/@content)').extract_first()),
            'ref': response.url
        }

        opening_hours = self.parse_hours(response.xpath(
            '//div[@class="Nap-column Nap-column--3"]//div/div/table/tbody/tr[@class="c-location-hours-details-row js-day-of-week-row highlight-text"]'))
        if opening_hours:
            properties['opening_hours'] = opening_hours
        yield GeojsonPointItem(**properties)

    def parse_city_stores(self, response):
        stores = response.xpath("//a[@class='Teaser-nearbyLink Link']/@href").extract()
        for store in stores:
            yield scrapy.Request(response.urljoin(store), callback=self.parse_store)

    def parse_city(self, response):
        city_urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()

        for city_url in city_urls:
            if city_url.count('/') >= 2:
                yield scrapy.Request(response.urljoin(city_url), callback=self.parse_store)
            else:
                yield scrapy.Request(response.urljoin(city_url), callback=self.parse_city_stores)

    def parse(self, response):
        state_urls = response.xpath('//div[@class="c-directory-list-content-wrapper"]/ul/li/a/@href').extract()
        for state_url in state_urls:
            yield scrapy.Request(response.urljoin(state_url), callback=self.parse_city)
