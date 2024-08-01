import io
import re
import zipfile

import scrapy

from locations.items import Feature


class ThalesFRSpider(scrapy.Spider):
    name = "thales_fr"
    item_attributes = {"brand": "Thales", "brand_wikidata": "Q1161666"}
    allowed_domains = ["google.com"]
    start_urls = ["https://www.google.com/maps/d/kml?mid=zOpSQcuS01RE.kLfnXlw7pPcM"]

    def parse(self, response):
        kmz = zipfile.ZipFile(io.BytesIO(response.body))
        kml = kmz.open(kmz.filelist[0]).read()
        data = scrapy.Selector(text=kml, type="xml")
        data.remove_namespaces()
        for ref, placemark in enumerate(data.xpath("//Placemark")):
            yield self.parse_location(ref, placemark)

    def parse_location(self, ref, placemark):
        addr = re.search(
            "Address: (.*?)<br>",
            placemark.xpath(".//description/text()").extract_first(),
        )[1]
        if "France" not in addr:
            street = locality = postal = ""
        else:
            addr_split = addr.split(",")
            if len(addr_split) == 4:
                street = addr_split[0] + addr_split[1]
                postal = re.search(r"\d{5}", addr_split[2]).group(0)
                locality = ""
            else:
                street = addr_split[0]
                postal = re.search(r"\d{5}", addr_split[1]).group(0)
                locality = addr_split[1].replace(postal, "").strip()

        x, y, z = placemark.xpath(".//coordinates/text()").extract_first().strip().split(",")

        properties = {
            "ref": ref,
            "name": placemark.xpath(".//name/text()").extract_first(),
            "street_address": street,
            "city": locality,
            "postcode": postal,
            "country": "FR",
            "lat": y,
            "lon": x,
        }

        return Feature(**properties)
