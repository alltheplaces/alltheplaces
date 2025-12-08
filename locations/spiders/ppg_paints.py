import re
import urllib

import scrapy

from locations.items import Feature


class PpgPaintsSpider(scrapy.Spider):
    name = "ppg_paints"
    item_attributes = {"brand": "PPG Paints", "brand_wikidata": "Q83891559"}
    allowed_domains = ["www.ppgpaints.com"]
    start_urls = [
        "https://www.ppgpaints.com/store-locator/us",
        "https://www.ppgpaints.com/store-locator/ca",
        "https://www.ppgpaints.com/store-locator/mx",
    ]

    def parse(self, response):
        for href in response.xpath('//*[@class="store-locations-item"]//@href').extract():
            url = response.urljoin(href)
            yield scrapy.Request(url)
        for href in response.xpath('//*[@id="store-table"]//@href').extract():
            url = response.urljoin(href)
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        map_url = re.search(r"url\('(.*)'\);", response.css(".store-staticmap").attrib["style"]).group(1)
        [latlng] = urllib.parse.parse_qs(urllib.parse.urlparse(map_url).query)["center"]
        lat, lon = map(float, latlng.split(","))
        properties = {
            "ref": response.xpath('//*[@itemprop="name"]/@href').get(),
            "lat": lat,
            "lon": lon,
            "website": response.url,
            "name": response.xpath('//*[@itemprop="name"]/text()').get(),
            "street_address": response.xpath('//*[@itemprop="streetAddress"]/text()').get(),
            "city": response.xpath('//*[@itemprop="addressLocality"]/text()').get(),
            "state": response.xpath('//*[@itemprop="addressRegion"]/text()').get(),
            "postcode": response.xpath('//*[@itemprop="postalCode"]/text()').get(),
            "phone": response.xpath('//*[@itemprop="telephone"]/text()').get(),
            "country": response.url.split("/")[4].upper(),
        }
        return Feature(**properties)
