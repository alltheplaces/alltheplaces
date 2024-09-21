import re

from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature


class FiveBelowSpider(SitemapSpider):
    name = "five_below"
    item_attributes = {"brand": "Five Below", "brand_wikidata": "Q5455836"}
    allowed_domains = ["locations.fivebelow.com"]
    sitemap_urls = ["https://locations.fivebelow.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.fivebelow.com/\S+", "parse_store")]

    def parse_store(self, response):
        store = response.xpath('//*[@itemtype="http://schema.org/Store"]')
        if not store:
            # The sitemap includes some URLs that do not provide details of individual stores
            return

        address = store.xpath("//*/address")
        geocoordinates = address.xpath('//*[@itemtype="http://schema.org/GeoCoordinates"]')
        postaladdress = address.xpath('//*[@itemtype="http://schema.org/PostalAddress"]')

        properties = {
            "ref": response.url,
            "name": "{} {}".format(
                store.xpath('//*/span[@class="Hero-locationName"]/text()').get(),
                store.xpath('//*/span[@class="Hero-locationGeo"]/text()').get(),
            ),
            "street_address": postaladdress.xpath('//*[@itemprop="streetAddress"]/@content').get(),
            "city": postaladdress.xpath('//*[@itemprop="addressLocality"]/@content').get(),
            "state": postaladdress.xpath('//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": postaladdress.xpath('//*[@itemprop="postalCode"]/text()').get(),
            "country": postaladdress.xpath('//*[@itemprop="addressCountry"]/text()').get(),
            "lon": float(geocoordinates.xpath('//*/meta[@itemprop="longitude"]/@content').get()),
            "lat": float(geocoordinates.xpath('//*/meta[@itemprop="latitude"]/@content').get()),
            "phone": postaladdress.xpath('//*[@itemprop="telephone"]/text()').get(),
            "website": response.url,
        }

        opening_hours = self.parse_hours(response)
        if opening_hours:
            properties["opening_hours"] = opening_hours

        yield Feature(**properties)

    def parse_hours(self, response):
        opening_hours = OpeningHours()

        store = response.xpath('//*[@itemtype="http://schema.org/Store"]')
        if store:
            # If holiday hours are currently in effect, you may see also see holiday openingHours specified
            # in the HTML, but they should appear outside of the <div class="Core-hours" />.
            all_hours = store.xpath('//*/div[@class="Core-hours"]//*[@itemprop="openingHours"]')
            regex = re.compile(r"(Su|Mo|Tu|We|Th|Fr|Sa)\s+(\d{2}:\d{2})\s*-(\d{2}:\d{2})")
            for hours in all_hours:
                hours_str = hours.get().strip()
                match = re.search(regex, hours_str)
                if match:
                    day_of_week = match.group(1)
                    open_time = match.group(2)
                    close_time = match.group(3)

                    if close_time == "00:00":
                        close_time = "23:59"

                    opening_hours.add_range(day=day_of_week, open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()
