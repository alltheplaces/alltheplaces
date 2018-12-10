import scrapy
import re
import urllib.parse

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class BanfieldPetHospitalScraper(scrapy.Spider):
    name = "banfield_pet_hospital"
    allowed_domains = ["www.banfield.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.banfield.com/our-hospitals/hospital-locations/all-locations',
    )

    def parse_store(self, response):

        elem = response.xpath('//div[contains(@class, "our-hospitals-location")]')

        script_body = ' '.join(elem.xpath('.//script/text()').extract())
        match = re.search(r'.*google.maps.LatLng\(([0-9.-]+),\s([0-9.-]+)\)', script_body)

        lat, lon = match.groups()

        # use last 3 elements of the store url as unique identifier (store number does not appear to be unique)
        ref = "_".join(urllib.parse.urlsplit(response.url).path.split('/')[-3:])

        number = elem.xpath('//div[@class="vcard"]/p[@id="hospitalAddressHospitalNumber"]/text()').extract_first()
        number = re.search(r'Hospital\sNumber:\s+(\d+)', number).group(1)

        properties = {
            'name': elem.xpath('//div[@class="vcard"]/p[@class="fn"]/text()').extract_first(),
            'addr_full': elem.xpath('//div[@class="vcard"]/span[@class="street-address"]/text()').extract_first(),
            'phone': elem.xpath('//div[@class="vcard"]/p[@id="hospitalAddressPhone"]/text()').extract_first(),
            'city': elem.xpath('//div[@class="vcard"]/span[@class="region"]/text()').extract_first(),
            'state': elem.xpath('//div[@class="vcard"]/span[@class="state"]/text()').extract_first(),
            'postcode': elem.xpath('//div[@class="vcard"]/span[@class="postal-code"]/text()').extract_first(),
            'ref': ref,
            'website': response.url,
            'lat': lat,
            'lon': lon,
            'extras': {
                'number': number
            }
        }

        days = elem.xpath('//div[@class="hours"]/div[contains(@class, "day")]/@content').extract()
        opening_hours = OpeningHours()

        for d in days:
            match = re.search(r'([A-Za-z]{2})\s([\d:]+)-([\d:]+)', d)
            if match:
                day, open, close = match.groups()
                opening_hours.add_range(day=day, open_time=open, close_time=close)

        hours = opening_hours.as_opening_hours()

        if hours and hours != 'Mo-Su ':
            properties['opening_hours'] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        stores = response.xpath('//li/table')
        for store in stores:
            elem = store.xpath('.//td[@class="hospname"]/a')
            path = elem.xpath('.//@href').extract_first()
            name = elem.xpath('.//text()').extract_first()

            yield scrapy.Request(response.urljoin(path), callback=self.parse_store)
