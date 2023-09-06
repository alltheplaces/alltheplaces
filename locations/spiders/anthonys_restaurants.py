import json
import re

import scrapy

from locations.items import Feature


class AnthonysRestaurantsSpider(scrapy.Spider):
    name = "anthonys_restaurants"
    item_attributes = {"brand": "Anthony's", "country": "US"}
    allowed_domains = ["www.anthonys.com"]
    start_urls = ("https://www.anthonys.com/restaurants/",)
    requires_proxy = True

    def parse(self, response):
        script = response.css("#acf-block-locations-map-script-js-extra::text").get()
        j = json.loads(script[script.find("{") : 1 + script.rfind("}")])
        for row in j["restaurants"]:
            meta = {"json": row}
            yield scrapy.Request(row["link"], meta=meta, callback=self.parse_location)

    def parse_location(self, response):
        json_data = response.meta["json"]
        address = json_data["address"]
        # decode entities
        name = scrapy.Selector(text=json_data["name"]).xpath("//text()").get()

        # These are weird enough that there's no hope of parsing them, but
        # clean the text up
        hours = response.xpath('//strong[text()="Hours:"]/../text()').extract()
        hours = ";".join(s.strip().replace("\xa0", " ") for s in hours)

        properties = {
            "ref": re.search(r"postid-(\d+)", response.css("body").attrib["class"])[1],
            "lat": address["latitude"],
            "lon": address["longitude"],
            "street_address": address["address"],
            "city": address["city"],
            "state": address["state"],
            "postcode": address["zip_code"],
            "name": name,
            "website": response.url,
            "phone": (response.xpath("//*[starts-with(@href, 'tel:')]/@href").get() or "")[4:],
            "opening_hours": hours,
        }
        return Feature(**properties)
