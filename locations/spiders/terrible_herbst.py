import scrapy

from locations.items import Feature


class TerribleHerbstSpider(scrapy.Spider):
    name = "terrible_herbst"
    item_attributes = {"brand": "Terrible Herbst", "brand_wikidata": "Q7703648"}
    allowed_domains = ["google.com"]
    start_urls = [
        "https://www.google.com/maps/d/u/0/kml?mid=17KgQXKUbt-foi_HwjRewevjQtKwwkz1d&lid=fbhMYyAMWfQ&forcekml=1",
    ]

    def parse(self, response):
        response.selector.remove_namespaces()

        for place in response.xpath("//Placemark"):
            self.logger.info(place.get())
            city_state = place.xpath('.//Data[@name="CITY/STATE"]/value/text()').get().split(",")

            city = city_state[0]
            state = city_state[1] if len(city_state) > 1 else None

            features = (place.xpath('.//Data[@name="FEATURES"]/value/text()').get() or "").lower()

            yield Feature(
                ref=place.xpath("name/text()").get(),
                name=place.xpath("name/text()").get(),
                addr_full=place.xpath('.//Data[@name="STREET ADDRESS"]/value/text()').get(),
                postcode=place.xpath('.//Data[@name="ZIP CODE"]/value/text()').get(),
                city=city.strip(),
                state=state and state.strip(),
                country="US",
                phone=place.xpath('.//Data[@name="TELEPHONE #"]/value/text()').get(),
                extras={
                    "amenity:fuel": True,
                    "amenity:chargingstation": "ev charging" in features,
                    "car_wash": "car wash" in features,
                },
            )
