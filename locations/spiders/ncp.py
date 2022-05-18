# -*- coding: utf-8 -*-
import json
import scrapy
from locations.items import GeojsonPointItem


class NcpSpider(scrapy.Spider):
    name = "ncp"
    item_attributes = {"brand": "National Car Parks", "brand_wikidata": "Q6971273"}
    allowed_domains = ["www.ncp.co.uk"]
    start_urls = ("https://www.ncp.co.uk/parking-solutions/cities/",)

    def parse(self, response):
        cities = response.xpath('//div[@class="city-tabs"]//ul/li/a/@href').extract()
        for city in cities:
            yield response.follow(city, self.parse_city)

    def parse_city(self, response):
        carparks = response.xpath(
            '//table[@class="airportListing large-stacktable"]/tbody/tr/td[1]/a/@href'
        ).extract()
        for carpark in carparks:
            yield response.follow(carpark, self.parse_carpark)

    def parse_carpark(self, response):
        js = response.xpath(
            '//article[@class="content"]//script[1]/text()'
        ).extract_first()
        data = self.parse_js(js)
        carpark = data["carparks"][0]
        location = data["location"]
        properties = {
            "ref": carpark["carParkCode"],
            "name": carpark["carParkTitle"],
            "addr_full": self.get_address(carpark),
            "city": carpark["addressLine4"],
            "country": "United Kingdom",
            "postcode": f"{carpark['postcodePart1']} {carpark['postcodePart2']}",
            "lat": location["coords"]["lat"],
            "lon": location["coords"]["lng"],
            "phone": carpark["telephoneNumber"],
            "opening_hours": carpark["openHours"].strip(),
            "website": response.url,
        }
        yield GeojsonPointItem(**properties)

    def parse_js(self, js_string):
        """
        hammer a known snippet of javascript of the form

        ```
        var detailsItem = {
            'element'       : "map-canvas-84401-23832-61805",
            'carparks'      : [{"metaID":466...}],
            'location'      : {"title":"Bradford Hall Ings"...}},
            'autocarpark'   : null
        };

        detailsArr.push(detailsItem);
        ```

        until we can parse it as json, then parse it
        """
        js = (
            js_string.replace("var detailsItem = ", "")
            .replace("detailsArr.push(detailsItem);", "")
            .strip()
            .rstrip(";")
        )
        expected_keys = ["element", "carparks", "location", "autocarpark"]
        for key in expected_keys:
            js = js.replace(f"'{key}'", f'"{key}"')
        return json.loads(js)

    def get_address(self, record):
        return ", ".join(
            [
                line
                for line in [
                    record["addressLine1"],
                    record["addressLine2"],
                    record["addressLine3"],
                ]
                if line
            ]
        )
