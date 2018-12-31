import datetime
import json
import scrapy
import re


from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AshleyHomeStoreSpider(scrapy.Spider):

    name = "ashleyhomestore"
    allowed_domains = [
        "ashleyfurniture.com",
        "ashleyhomestore.ca",
        "stores.boldapps.net"
    ]
    download_delay = 0.5

    def start_requests(self):
        return [
            scrapy.Request('https://stores.ashleyfurniture.com/store', callback=self.parse_us_stores),
            scrapy.Request('https://ashleyhomestore.ca/apps/store-locator', callback=self.parse_ca_stores),
        ]

    def parse_phone_number(self, phone):
        phone = phone.replace('+1', '')
        return '{0}-{1}-{2}'.format(phone[0:3], phone[3:6], phone[6:])

    def parse_hours(self, days):
        opening_hours = OpeningHours()

        for item in days:
            if item.xpath('./span[contains(@class, "hours")]/text()').extract_first() == "Closed":
                continue
            day = item.xpath('./span[contains(@class, "text")]/text()').extract_first()[:2]
            hours = item.xpath('./span[contains(@class, "hours")]/span/text()').extract_first()
            if hours == "Closed":
                continue
            open_time, close_time = hours.split('-')
            opening_hours.add_range(day=day,
                                    open_time=datetime.datetime.strptime(open_time, '%I:%M%p').strftime('%H:%M'),
                                    close_time=datetime.datetime.strptime(close_time, '%I:%M%p').strftime('%H:%M'))

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        # Panama City, FL store redirects to the main location search page; presumably the location no longer exists
        if response.url == 'https://stores.ashleyfurniture.com/':
            return

        data = "".join(response.xpath(
            '//body[contains(@class, "location-details")]//div[@class="container"]/text()').extract()).strip()
        if not data:
            # sometimes the data we need is in a script element
            data = "".join(
                response.xpath('//body[contains(@class, "location-details")]//div[@class="container"]//script/text()').extract()).strip()

        country = re.search(r'"addressCountry":\s+"(.+)"', data).group(1)
        locality = re.search(r'"addressLocality":\s+"(.+)"', data).group(1)
        region = re.search(r'"addressRegion":\s+"(.+)"', data).group(1)
        postal_code = re.search(r'"postalCode":\s+"(.+)"', data).group(1)
        street_address = re.search(r'"streetAddress":\s+"(.+)"', data).group(1)

        properties = {
            'addr_full': street_address,
            'name': response.xpath('//p[@class="store-name"]/text()').extract_first(),
            'phone': self.parse_phone_number(response.xpath('//a[@class="phone"]/text()').extract_first().strip()),
            'city': locality,
            'country': country,
            'state': region,
            'postcode': postal_code,
            'ref': "_".join(response.url.split('/')[-3:]),
            'website': response.url,
            'lat': float(response.xpath('//div[@id="location-details"]/@data-lat').extract_first()),
            'lon': float(response.xpath('//div[@id="location-details"]/@data-lng').extract_first()),
        }

        opening_hours = self.parse_hours(response.xpath('//div[@id="storeHours"]/div[contains(@class, "day")]'))

        if opening_hours:
            properties['opening_hours'] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse_store_list(self, response):
        urls = response.xpath('//div[contains(@class, "city-details")]/div[@class="storeName"]/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store)

    def parse_us_stores(self, response):
        urls = response.xpath('//div[@class="state-col"]/a/@href').extract()
        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_store_list)

    def parse_ca_store(self, response):
        properties = response.meta["properties"]

        data = json.loads(response.body_as_unicode())["data"]
        hours = scrapy.Selector(text=data).xpath('//span[@class="hours"]/text()').extract()
        pattern = re.compile(r'([a-z]+)\s*:\s*(.*)', re.IGNORECASE)

        opening_hours = OpeningHours()
        for hour in hours:
            hour = hour.strip()
            day, open_close = re.search(pattern, hour).groups()
            if open_close == "Closed":
                continue
            open_time, close_time = open_close.split('-')
            opening_hours.add_range(day=day[:2],
                                    open_time=datetime.datetime.strptime(open_time, '%I:%M%p').strftime('%H:%M'),
                                    close_time=datetime.datetime.strptime(close_time, '%I:%M%p').strftime('%H:%M'))
        opening_hours = opening_hours.as_opening_hours()

        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def parse_ca_stores(self, response):
        store_list = response.xpath('//div[@class="addresses"]/ul/li')

        # coords are found in script element and match to store by a unique id
        scripts = "".join(response.xpath('//script/text()').extract())
        markers = re.findall(r'markersCoords.push\((.+?)\);', scripts)

        coords = {}
        lat_pattern = re.compile(r'lat:\s*([0-9.-]+)')
        lon_pattern = re.compile(r'lng:\s*([0-9.-]+)')
        id_pattern = re.compile(r'id:\s*([0-9]+)')
        for marker in markers:
            try:
                lat = re.search(lat_pattern, marker).group(1)
                lon = re.search(lon_pattern, marker).group(1)
            except AttributeError:
                continue
            id = re.search(id_pattern, marker).group(1)
            coords[id] = {"lat": float(lat), "lon": float(lon)}

        for store in store_list:
            id = store.xpath('./@onmouseover').re_first('\((.*)\)')
            name = store.xpath('.//span[@class="name"]/text()').extract_first().strip()
            name = re.sub(r'\(\d+\)', '', name).strip()

            properties = {
                "ref": id,
                "name": name,
                "addr_full": store.xpath('.//span[@class="address"]/text()').extract_first().strip(),
                "city": store.xpath('.//span[@class="city"]/text()').extract_first().strip(),
                "state": store.xpath('.//span[@class="prov_state"]/text()').extract_first().strip(),
                "postcode": store.xpath('.//span[@class="postal_zip"]/text()').extract_first().strip(),
                "country": 'CA',
                "phone": store.xpath('.//span[@class="phone"]/text()').extract_first().strip(),
                "lat": float(coords[id]["lat"]),
                "lon": float(coords[id]["lon"])
            }

            yield scrapy.Request(url='https://stores.boldapps.net/front-end/get_store_info.php?shop=ashley-homestores-in-canada.myshopify.com&data=detailed&store_id=' + str(id),
                                 callback=self.parse_ca_store,
                                 meta={"properties": properties})
