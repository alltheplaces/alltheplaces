import scrapy

from locations.items import Feature


class RoadRangerSpider(scrapy.Spider):
    name = "road_ranger"
    item_attributes = {"brand": "Road Ranger"}
    allowed_domains = ["www.roadrangerusa.com"]
    start_urls = ("https://www.roadrangerusa.com/locations-amenities/find-a-road-ranger",)

    def parse(self, response):
        rows = response.xpath('//li[@class="store-location-row"]')

        for row in rows:
            # address is like '1615 EAST MAIN STREET, GREENWOOD IN'
            address = row.xpath('.//h4[@class="store-location-teaser__address"]/text()').extract_first().strip()
            # split house number/road from city/state
            addr_full, city_state = address.rsplit(",", 1)
            # assume state is the last non-whitespace thing and
            # the rest is the city
            city, state = city_state.rsplit(" ", 1)
            phone = row.xpath('.//a[contains(@href, "tel:")]/@href').extract_first()
            phone = phone.split(":", 1)[1]  # strip off the leading 'tel:'
            # coordinates is basically 'Coordinates: <lat>, <lng>'
            coordinates = row.xpath('.//span[@class="coordinates"]/text()').extract_first()
            latitude, longitude = coordinates.split(":", 1)[1].split(",")

            properties = {
                "ref": address,
                "phone": phone.strip(),
                "addr_full": addr_full.strip(),
                "city": city.strip(),
                "state": state.strip(),
                "name": "Road Ranger",
                "lon": float(longitude),
                "lat": float(latitude),
            }
            yield Feature(**properties)
