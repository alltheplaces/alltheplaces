import scrapy
from scrapy.selector.unified import Selector

from locations.items import GeojsonPointItem


class CoenMarketsSpider(scrapy.Spider):
    name = "coen_markets"
    item_attributes = {"name": "Coen", "brand": "Coen Markets"}
    start_urls = ["https://coen1923.com/locations/search"]

    def parse(self, response):
        for location in response.json()["locations"]:
            if not location:
                continue
            url_title = location["url_title"]
            # Note: embedded in an iframe; not useful as item's website
            store_url = f"https://coen1923.com/locations/location/{url_title}"
            yield scrapy.Request(store_url, self.parse_store, cb_kwargs={"js": location})

    def parse_store(self, response, js):
        props = {}
        props["addr_full"] = Selector(text=js["address"]).xpath("//p/text()").get()
        props["ref"] = js["url_title"]
        props["lat"] = js["coordinates"][0]
        props["lon"] = js["coordinates"][1]
        props["city"] = js["city"]
        props["state"] = js["state"]
        props["postcode"] = js["zip"]
        props["phone"] = js["phone_number"]
        hours = response.css(".hours p:not(:empty)").xpath("text()").get()
        props["opening_hours"] = hours
        return GeojsonPointItem(**props)
