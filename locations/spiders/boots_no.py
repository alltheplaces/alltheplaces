import re
import urllib.parse

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class BootsNOSpider(scrapy.Spider):
    name = "boots_no"
    item_attributes = {"brand": "Boots", "brand_wikidata": "Q6123139"}
    allowed_domains = ["apotek.boots.no", "zpin.it"]
    download_delay = 0.5
    start_urls = [
        "https://apotek.boots.no",
    ]

    def parse_map(self, response):
        map_data = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "google.maps.LatLng")]/text()'
        ).extract_first()
        coordinates = re.search(r"var latlng \= new google\.maps\.LatLng\((.*)\)", map_data).group(1)
        lat, lon = coordinates.split(",")

        properties = {
            "ref": response.meta["ref"],
            "name": response.meta["name"],
            "addr_full": response.meta["addr_full"],
            "country": response.meta["country"],
            "lat": lat,
            "lon": lon,
            "phone": response.meta["phone"],
            "website": response.meta["website"],
        }

        apply_category(Categories.PHARMACY, properties)
        yield Feature(**properties)

    def parse_store(self, response):
        ref = re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1)
        address_parts = response.xpath('//div[contains(text(),"Besøksadresse")]/following-sibling::text()').extract()
        address = " ".join(map(str.strip, address_parts))
        name = urllib.parse.unquote_plus(re.search(r".+/(.+?)/(.+?)/?(?:\.html|$)", response.url).group(1))
        phone = response.xpath('//a[contains(@href,"tel")]/text()').extract_first()

        map_url = "https://zpin.it/on/location/map/?key=440558&id={store_id}".format(store_id=ref)

        meta_props = {
            "ref": ref,
            "name": name,
            "addr_full": address,
            "country": "NO",
            "phone": phone,
            "website": response.url,
        }

        yield scrapy.Request(map_url, meta=meta_props, callback=self.parse_map)

    def parse(self, response):
        urls = response.xpath('//div[@id="mapAsList"]//a/@href').extract()

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
