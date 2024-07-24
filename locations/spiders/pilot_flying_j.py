import json

import scrapy

from locations.items import Feature


class PilotFlyingJSpider(scrapy.Spider):
    name = "pilot_flying_j"
    item_attributes = {"brand": "Pilot Flying J", "brand_wikidata": "Q1434601"}
    allowed_domains = ["pilotflyingj.com"]

    start_urls = ["https://locations.pilotflyingj.com/"]

    def parse(self, response):
        for href in response.xpath('//a[@data-ya-track="todirectory" or @data-ya-track="visitpage"]/@href').extract():
            yield scrapy.Request(response.urljoin(href))

        for item in response.xpath('//*[@itemtype="http://schema.org/LocalBusiness"]'):
            yield from self.parse_store(response, item)

    def parse_store(self, response, item):
        jsdata = json.loads(item.xpath('.//script[@class="js-map-config"]/text()').get())
        store = jsdata["entities"][0]["profile"]
        properties = {
            "ref": store["meta"]["id"],
            "lat": item.xpath('//*[@itemprop="latitude"]/@content').get(),
            "lon": item.xpath('//*[@itemprop="longitude"]/@content').get(),
            "name": store["name"],
            "website": response.url,
            "street_address": store["address"]["line1"],
            "city": store["address"]["city"],
            "state": store["address"]["region"],
            "postcode": store["address"]["postalCode"],
            "country": store["address"]["countryCode"],
            "phone": store.get("mainPhone", {}).get("number"),
            "extras": {
                "fax": store.get("fax", {}).get("number"),
                "amenity": "fuel",
                "fuel:diesel": "yes",
                "fuel:HGV_diesel": "yes",
                "hgv": "yes",
            },
        }
        properties.update(self.brand_info(store["name"]))
        yield Feature(**properties)

    def brand_info(self, name):
        if "Pilot" in name:
            return {"brand": "Pilot", "brand_wikidata": "Q7194412"}
        elif "Flying J" in name:
            return {"brand": "Flying J", "brand_wikidata": "Q64130592"}
        else:
            return {"brand": name}
