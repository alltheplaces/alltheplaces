import re

import scrapy

from locations.items import Feature


class TexaidBGSpider(scrapy.Spider):
    name = "texaid_bg"
    item_attributes = {"brand": "Texaid", "brand_wikidata": "Q1395183"}
    allowed_domains = ["texaidbg.texaid.com"]
    start_urls = ["https://texaidbg.texaid.com/bg/kontejneri-za-sbirane.html"]
    no_refs = True

    def parse(self, response):
        js = response.xpath('//script[contains(text(), "L.marker")]').get()
        marker_regex = r"L\.marker\(\[(\d+\.\d+),\s*(\d+\.\d+)\].*?bindPopup\(\"(.*?)\"\)"
        markers = re.findall(marker_regex, js)
        for lat, lon, popup in markers:
            properties = {
                "lon": float(lon),
                "lat": float(lat),
                "street_address": popup,
            }
            yield Feature(**properties)
