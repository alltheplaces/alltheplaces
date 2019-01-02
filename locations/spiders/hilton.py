import json
import re
import scrapy

from locations.items import GeojsonPointItem


class HiltonSpider(scrapy.Spider):
    name = "hilton"
    allowed_domains = ["hilton.com", "hiltongrandvacations.com"]

    def start_requests(self):
        sites = [
            ('Hilton', 'https://www3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Waldorf Astoria', 'https://waldorfastoria3.hilton.com/en/hotels/index.html', self.parse_hotel_list),
            ('LXR', 'https://lxrhotels3.hilton.com/lxr/locations/', self.parse_lxr),
            ('Conrad', 'https://conradhotels3.hilton.com/en/hotels/index.html', self.parse_hotel_list),
            ('Canopy', 'https://canopy3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Curio Collection', 'https://curiocollection3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Doubletree', 'https://doubletree3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Tapestry', 'https://tapestrycollection3.hilton.com/tc/locations/',  self.parse_tapestry),
            ('Embassy Suites', 'https://embassysuites3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Hilton Garden Inn', 'https://hiltongardeninn3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Hampton Inn', 'https://hamptoninn3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Tru', 'https://tru3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Homewood Suites', 'https://homewoodsuites3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Home 2 Suites', 'https://home2suites3.hilton.com/en/hotel-locations/index.html', self.parse),
            ('Hilton Grand Vacations', 'https://www.hiltongrandvacations.com/destinations/', self.parse_grand_vacation),
            # ('Motto', '', None)  # no locations yet but "coming soon"
        ]
        for site in sites:
            yield scrapy.Request(url=site[1], callback=site[2])

    def parse_hotel_list(self, response):
        """Different style hotel list"""
        hotel_urls = response.xpath('//ul[@class="locations"]/li/a/@href').extract()

        for url in hotel_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_hotel)

    def parse_lxr(self, response):
        """Parse LXR hotel list"""
        hotel_urls = response.xpath('//section[contains(@class, "location-hotels-wrap")]/section//a/@href').extract()

        for url in hotel_urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_lxr_hotel)

    def parse_lxr_hotel(self, response):
        """Parse LXR hotel page (address parts are not labeled correctly)"""
        address = ", ".join([response.xpath('//span[@itemprop="streetAddress"]/text()').extract_first(),
                             response.xpath('//span[@itemprop="addressRegion"]/text()').extract_first()])

        properties = {
            "name": response.xpath('//span[@itemprop="name"]/text()').extract_first(),
            "ref": response.xpath('//link[@rel="canonical"]/@href').re_first('.*/(.*?)/'),
            "phone": response.xpath('//span[@itemprop="telephone"]//span/text()').extract_first(),
            "addr_full": address,
            "city": response.xpath('//span[@itemprop="addressCountry"]/text()').extract_first(),
            "country": response.xpath('//span[@itemprop="postalCode"]/text()').extract_first().strip(),
            "website": response.xpath('//link[@rel="canonical"]/@href').extract_first(),
            "lat": float(response.xpath('//div[@class="marker"]/@data-lat').extract_first()),
            "lon": float(response.xpath('//div[@class="marker"]/@data-lng').extract_first())
        }
        yield GeojsonPointItem(**properties)

    def parse_tapestry(self, response):
        """Parse Tapestry Collection hotel list"""
        hotels = json.loads(response.xpath('//script').re_first('locationsResult\s*=\s*(.*);'))

        for hotel in hotels:
            properties = {
                "ref": hotel["id"],
                "name": hotel["hotel_name"],
                "state": hotel["location"]
            }

            yield scrapy.Request(url=response.urljoin(hotel["pagelink"]),
                                 callback=self.parse_tapestry_hotel,
                                 meta={"properties": properties})

    def parse_tapestry_hotel(self, response):
        """Parse Tapestry hotel page"""
        properties = response.meta["properties"]

        map_data = json.loads(response.xpath('//script/text()').re_first(r'map_vars\s*=\s*(.*);'))

        properties.update({
            "addr_full": response.xpath('//p[@class="address-info-text"]/text()').extract_first().strip(),
            "phone": response.xpath('//a[contains(@class, "location-icon-phone")]/span/text()').extract_first(),
            "website": response.url,
            "lat": float(map_data["lat"]),
            "lon": float(map_data["lng"])
        })
        yield GeojsonPointItem(**properties)

    def parse_grand_vacation_hotel(self, response):
        """Parse Grand Vacation hotel resort page"""
        properties = response.meta["properties"]
        lat, lon = response.xpath('//script/text()').re_first('.*google.maps.LatLng\(\s*(.*)\s+\);').split(',')
        properties.update({
            "name": response.xpath('//div[contains(@class, "resort-title")]//h1/text()').extract_first(),
            "ref":  "_".join(re.search(r'.*/(.*)/(.*)/', response.url).groups()),
            "lat": float(lat),
            "lon": float(lon),
            "website": response.url
        })
        yield GeojsonPointItem(**properties)

    def parse_grand_vacation(self, response):
        """Parse Hilton Grand Vacations resort list"""
        resorts = response.xpath('//div[contains(@class, "resortpanel")]')

        for resort in resorts:
            url = resort.xpath('.//a/@href').extract_first()
            location = resort.xpath('.//p[@class="location"]/text()').extract_first().split(',')
            properties = dict()
            properties["country"] = location.pop().strip()
            properties["state"] = location.pop().strip()
            properties["city"] = ", ".join(location)

            yield scrapy.Request(response.urljoin(url),
                                 callback=self.parse_grand_vacation_hotel,
                                 meta={"properties": properties})

    def parse_hotel(self, response):
        """Parse generic hotel page"""
        lat, lon = response.xpath('//meta[@name="geo.position"]/@content').extract_first().split(';')

        properties = {
            "name": response.xpath('//meta[@name="og:title"]/@content').extract_first(),
            "ref": re.search(r'.*/(.*)/index.html', response.url).group(1),
            "phone": response.xpath('//span[@class="property-telephone"]/text()').extract_first(),
            "addr_full": response.xpath('//span[@class="property-streetAddress"]/text()').extract_first().strip(),
            "city": response.xpath('//span[@class="property-addressLocality"]/text()').extract_first(),
            "state": response.xpath('//span[@class="property-addressRegion"]/text()').extract_first(),
            "country": response.xpath('//span[@class="property-addressCountry"]/text()').extract_first(),
            "postcode": response.xpath('//span[@class="property-postalCode"]/text()').extract_first(),
            "lat": float(lat),
            "lon": float(lon),
            "website": response.url
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        """Parse generic hotel listings"""
        hotel_urls = response.xpath('//ul[@class="directory_hotels_list"]/li/a/@href').extract()
        if hotel_urls:
            for url in hotel_urls:
                yield scrapy.Request(response.urljoin(url), callback=self.parse_hotel)

        else:
            urls = response.xpath('//ul[@class="directory_locations_list"]/li/a/@href').extract()
            for url in urls:
                yield scrapy.Request(response.urljoin(url))
