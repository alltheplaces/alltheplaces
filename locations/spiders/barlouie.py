import json

import scrapy

from locations.items import GeojsonPointItem


class BarlouieSpider(scrapy.Spider):
    name = "barlouie"
    allowed_domains = ["www.barlouie.com"]
    start_urls = ["https://www.barlouie.com/locations"]
    item_attributes = {"brand": "Barlouie", "brand_wikidata": "Q16935493"}

    def parse(self, response):
        for link in response.xpath("//a[contains(@href, 'locations')]/@href").getall():
            yield scrapy.Request(
                "https://www.barlouie.com" + link, self.parse_each_website
            )

    def parse_each_website(self, response):
        for ldjson in response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract():
            sanitized_data = self.sanitize_json(ldjson)
            data = json.loads(sanitized_data)
            if data["@type"] == "Restaurant":
                yield self.parse_store(response, data)

    def sanitize_json(self, data):
        start_index = data.find('"TimeZoneOffsetSeconds"')
        end_index = data.find("]", start_index)
        return data[: start_index - 7] + data[end_index - 1 :]

    def parse_store(self, response, data):
        properties = {
            "name": data["name"],
            "ref": response.url.split("/")[-2],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "phone": data["telephone"],
            "opening_hours": "".join(data["openingHours"]),
            "website": response.url,
        }
        return GeojsonPointItem(**properties)
