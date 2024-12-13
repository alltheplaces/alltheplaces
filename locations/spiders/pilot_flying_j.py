import json

import scrapy

from locations.items import Feature

PILOT = {"brand": "Pilot", "brand_wikidata": "Q64128179"}
FLYING_J = {"brand": "Flying J", "brand_wikidata": "Q64130592"}
ONE9 = {"brand": "ONE9"}
TOWN_PUMP = {"brand": "Town Pump", "brand_wikidata": "Q7830004"}


class PilotFlyingJSpider(scrapy.Spider):
    name = "pilot_flying_j"
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
        if "Dealer" in store["name"]:
            return
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
        if name in ["Pilot Licensed Location", "Pilot Travel Center"]:
            return PILOT
        elif name in ["Flying J Licensed Location", "Flying J Travel Center"]:
            return FLYING_J
        elif name == "Pilot Licensed Location - Town Pump":
            return TOWN_PUMP
        elif name == "ONE9 Travel Center":
            return ONE9
        return {}
