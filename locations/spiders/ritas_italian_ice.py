import json

import scrapy

from locations.items import Feature


class RitasItalianIceSpider(scrapy.Spider):
    name = "ritas_italian_ice"
    item_attributes = {"brand": "Rita's Italian Ice", "brand_wikidata": "Q7336456"}
    allowed_domains = ["ritasice.com"]

    start_urls = ["https://www.ritasice.com/wpsl_stores-sitemap.xml"]

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        script = response.xpath('//script/text()[contains(.,"wpslMap_0")]').get()
        start = script.index("{", script.index("wpslMap_0"))
        data = json.decoder.JSONDecoder().raw_decode(script, start)[0]
        if not data["locations"]:
            # no json in about 9 of these
            return
        store = data["locations"][0]
        lat, lon = map(float, (store["lat"], store["lng"]))
        if lat < 0:
            lat, lon = lon, lat
        properties = {
            "ref": store["id"],
            "lat": lat,
            "lon": lon,
            "name": store["store"],
            "street_address": store["address"],
            "city": store["city"],
            "state": store["state"],
            "postcode": store["zip"],
            "country": store["country"],
            "phone": response.xpath('//*[@class="wpsl-phone-wrap"]//text()').get(),
            "website": response.url,
        }
        yield Feature(**properties)
