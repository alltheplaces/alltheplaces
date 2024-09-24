from scrapy import Selector
from scrapy.spiders import Spider

from locations.google_url import url_to_coords
from locations.items import Feature
from locations.spiders.debonairs_pizza_za import DEBONAIRS_SHARED_ATTRIBUTES


class DebonairsPizzaNASpider(Spider):
    name = "debonairs_pizza_na"
    item_attributes = DEBONAIRS_SHARED_ATTRIBUTES
    start_urls = ["https://namibia.debonairspizza.africa/contact/locate-us"]
    no_refs = True

    def parse(self, response):
        for location in response.xpath('.//a[contains(@href, "google.com/maps")]').getall():
            coords = url_to_coords(Selector(text=location).xpath(".//a/@href").get())
            properties = {
                "lat": coords[0],
                "lon": coords[1],
                "branch": Selector(text=location).xpath(".//a/text()").get(),
            }
            yield Feature(**properties)
