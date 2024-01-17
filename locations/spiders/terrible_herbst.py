import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
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
            item = Feature()

            city_state = place.xpath('.//Data[@name="CITY/STATE"]/value/text()').get().split(",")
            city = city_state[0]
            state = city_state[1] if len(city_state) > 1 else None

            features = (place.xpath('.//Data[@name="FEATURES"]/value/text()').get() or "").lower()

            item["ref"] = place.xpath("name/text()").get()
            item["name"] = place.xpath("name/text()").get()
            # Addresses are inconsistent, sometimes it's street address, sometimes full
            item["addr_full"] = place.xpath('.//Data[@name="STREET ADDRESS"]/value/text()').get()
            item["postcode"] = place.xpath('.//Data[@name="ZIP CODE"]/value/text()').get()
            item["city"] = city.strip()
            item["state"] = state and state.strip()
            item["country"] = "US"
            item["phone"] = place.xpath('.//Data[@name="TELEPHONE #"]/value/text()').get()
            apply_category(Categories.FUEL_STATION, item)
            apply_yes_no(Extras.CAR_WASH, item, "car wash" in features)
            # TODO: map EV charging on fuel stations properly
            if "ev charging" in features:
                pass

            yield item
