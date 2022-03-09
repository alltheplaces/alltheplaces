import scrapy
import re
from locations.items import GeojsonPointItem


class LavenecianaSpider(scrapy.Spider):
    name = "laveneciana"
    item_attributes = {"brand": "La Veneciana"}
    allowed_domains = ["www.laveneciana.com.ar"]
    download_delay = 0.5
    start_urls = ("http://www.laveneciana.com.ar/sucursales.html",)

    def parse(self, response):
        stores = response.xpath(
            '//div[@class="navigation-container"]/div[@id="thumbs"]/ul[@class="thumbs noscript"]/li'
        )
        for store in stores:
            addr_full_tel = store.xpath(
                'normalize-space(./div[@class="caption"]/div[@class="image-desc"]/text())'
            ).extract_first()
            location = store.xpath(
                'normalize-space(./div[@class="caption"]/div[@class="ubicacion"]/iframe/@src)'
            ).extract_first()
            position = re.findall(r"ll=[0-9-.,]+", location)
            id = re.findall(r"cid=[0-9]+", location)
            if len(position) > 0:
                lat = float(position[0][3:].split(",")[0])
                lon = float(position[0][3:].split(",")[1])
                id = id[0][4:]
            else:
                lat = ""
                lon = ""
                id = ""
            addr_full = addr_full_tel.split("Tel.: ")[0]
            phone_number = addr_full_tel.split("Tel.: ")[1]
            if addr_full != "Direccion... ":
                properties = {
                    "addr_full": addr_full,
                    "phone": phone_number,
                    "city": "",
                    "state": "",
                    "postcode": "",
                    "ref": id,
                    "website": response.url,
                    "lat": lat,
                    "lon": lon,
                }
                yield GeojsonPointItem(**properties)
