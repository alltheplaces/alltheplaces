import scrapy
import re
from urllib.parse import urlparse

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem

class DickeysBarbecuePitSpider(scrapy.Spider):
    name = "dickeys_barbecue_pit"
    allowed_domains = [ "dickeys.com" ]
    start_urls = (
        "https://www.dickeys.com/location/search-by-state",
    )

    def parse(self, response):
        directory_links = response.xpath('//a[@class="state-links"]/@href').extract()
        for link in directory_links:
            print(response.urljoin(link))
            yield scrapy.Request(
                response.urljoin(link),
                callback=self.parse
            )

        regex_phone_prefix = re.compile("^\s*Telephone\:\s*(.+)$")

        all_restaurants = response.xpath('//*[@itemtype="http://schema.org/Restaurant"]')
        for restaurant in all_restaurants:

            properties = {
                "name": restaurant.xpath('//*[@itemprop="name"]/text()').get(),
                "addr_full": restaurant.xpath('//*[@itemprop="streetAddress"]/text()').get(),
                "city": restaurant.xpath('//*[@itemprop="addressLocality"]/text()').get(),
                "state": restaurant.xpath('//*[@itemprop="addressRegion"]/text()').get(),
                "postcode": restaurant.xpath('//*[@itemprop="postalCode"]/text()').get(),
                "phone": restaurant.xpath('//a[starts-with(text(), "Telephone:")]/text()').get(),
                "website": response.url,
            }

            # URLs with details of all restaurants in a given city look like:
            # '/location/search-by-city/<num>/<city-name>', where:
            #
            # <num> appears to be a number associated with the state containing the city
            # <city-name> is the name of the city.
            #
            # Strip off the '/location/search-by-city' prefix, then append the name we found for each
            # restaurant.  Use this as the unique ID of the restaurant in the crawl, as no other
            # reliable ID seems to appear in the data.
            ref = urlparse(response.url).path.split('/', maxsplit=3)[3]
            properties['ref'] = '_'.join([ref, properties['name']])

            # If phone has a 'Telephone: ' prefix, strip it away.
            match_phone = re.search(regex_phone_prefix, properties['phone'])
            if match_phone:
                properties['phone'] = match_phone.groups()[0]

            # Some fields may have leading/trailing space.  We've seen that city often has both
            # trailing comma and space.
            for key in properties:
                properties[key] = properties[key].strip(', ')

            yield GeojsonPointItem(**properties)

