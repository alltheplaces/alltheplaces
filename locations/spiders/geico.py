import json
import re

import scrapy

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address

MAP_URL = "https://www.geico.com/public/php/geo_map.php?"


class GeicoSpider(scrapy.Spider):
    name = "geico"
    item_attributes = {"brand": "GEICO", "brand_wikidata": "Q1498689"}
    allowed_domains = ["www.geico.com"]
    start_urls = ["https://www.geico.com/sitemap.xml"]
    download_delay = 1.5

    def parse(self, response):
        response.selector.remove_namespaces()

        urls = response.xpath('//loc[contains(text(), "insurance-agents")]/text()').extract()

        for url in urls:
            if len(url.split("/")) > 7:  # location page
                yield scrapy.Request(url, callback=self.parse_location)

    def parse_location(self, response):
        script_data = response.xpath(
            '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
        ).extract_first()
        if script_data:
            data = json.loads(script_data)
            ref = "_".join(re.search(r".+/(.+?)/(.+?)/?(?:\.html|$)", response.url).groups())

            metadata = {
                "name": data["name"],
                "ref": ref,
                "street_address": data["address"]["streetAddress"],
                "city": data["address"]["addressLocality"],
                "state": data["address"]["addressRegion"],
                "postcode": data["address"]["postalCode"],
                "phone": data.get("telephone"),
                "website": data.get("url") or response.url,
            }
            address = clean_address(
                [
                    data["address"]["streetAddress"],
                    data["address"]["addressLocality"],
                    data["address"]["addressRegion"],
                    data["address"]["postalCode"],
                ]
            )

            form_data = {
                "address": address,
                "langauge": "en-US",
                "type": "Sales",
                "captcha": "false",
            }

            yield scrapy.http.FormRequest(
                url=MAP_URL,
                method="POST",
                formdata=form_data,
                meta=metadata,
                callback=self.parse_location_map,
            )

    def parse_location_map(self, response):
        data = json.loads(response.text)
        map_data = data[1]  # skip header element
        lat = map_data["latitude"]
        lon = map_data["longitude"]

        properties = {
            "ref": response.meta["ref"],
            "name": response.meta["name"],
            "street_address": response.meta["street_address"],
            "city": response.meta["city"],
            "state": response.meta["state"],
            "postcode": response.meta["postcode"],
            "lat": lat,
            "lon": lon,
            "phone": response.meta["phone"],
            "website": response.meta["website"],
        }

        yield Feature(**properties)
