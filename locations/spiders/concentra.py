import re
import scrapy
from locations.items import GeojsonPointItem
from scrapy.http import HtmlResponse


class ConcentraSpider(scrapy.Spider):
    name = "concentra"
    item_attributes = {"brand": "Concentra"}
    allowed_domains = ["concentra.com"]
    start_urls = (
        "https://www.concentra.com//sxa/search/results/?s={449ED3CA-26F3-4E6A-BF21-9808B60D936F}|{449ED3CA-26F3-4E6A-BF21-9808B60D936F}&sig=&v={D907A7FD-050F-4644-92DC-267C1FDE200C}&p=10000&g=45|-122&o=DistanceMi,Ascending",
    )

    def parse(self, response):
        data = response.json()
        stores = data["Results"]
        for store in stores:
            url = "https://www.concentra.com{}".format(store["Url"])

            lat, lon = None, None
            if "Geospatial" in store:
                geospatial = store["Geospatial"]
                if "Latitude" in geospatial:
                    lat = geospatial["Latitude"]
                if "Longitude" in geospatial:
                    lon = geospatial["Longitude"]

            # Most of the data is stored as an html blob inside the json
            # so build a new HtmlResponse from it which we can parse.
            html = HtmlResponse(url=url, body=store["Html"].encode("utf-8"))
            addr1 = html.xpath(
                '//div[@class="field-addressline1"]/text()'
            ).extract_first()
            addr2 = html.xpath(
                '//div[@class="field-addressline2"]/text()'
            ).extract_first()
            postcode = html.xpath(
                '//span[@class="field-zipcode"]/text()'
            ).extract_first()
            phone = html.xpath('//div[@class="field-mainphone"]/text()').extract_first()
            state = html.xpath(
                '//span[@class="field-stateabbreviation"]/text()'
            ).extract_first()
            city = html.xpath('//div[@class="field-centername"]/text()').extract_first()
            name = html.xpath(
                '//div[@class="location-clinic-link"]/a/@title'
            ).extract_first()

            if addr1:
                addr1 = addr1.strip()
            if addr2:
                addr2 = addr2.strip()

            addr_full = None
            if addr1 and addr2:
                addr_full = " ".join([addr1, addr2])
            elif addr1:
                addr_full = addr1

            properties = {}
            properties["ref"] = store["Id"]
            properties["website"] = url

            if addr_full:
                properties["addr_full"] = addr_full
            if name:
                properties["name"] = name
            if city:
                properties["city"] = city
            if state:
                properties["state"] = state
            if postcode:
                properties["postcode"] = postcode
            if phone:
                properties["phone"] = phone.replace(".", "-")
            if lat:
                properties["lat"] = lat
            if lon:
                properties["lon"] = lon

            yield GeojsonPointItem(**properties)
