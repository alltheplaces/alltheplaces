import scrapy
import xmltodict

from locations.items import Feature


class CrocsESSpider(scrapy.Spider):
    name = "crocs_es"
    item_attributes = {
        "brand": "Crocs",
        "brand_wikidata": "Q926699",
    }

    def start_requests(self):
        yield scrapy.Request(
            url="https://crocs.es/storefinder?ajax=1&all=1",
            method="POST",
        )

    def parse(self, response):
        json_data = xmltodict.parse(response.text)
        for data in json_data["markers"]["marker"]:
            properties = {
                "name": data["@name"],
                "addr_full": data["@addressNoHtml"],
                "email": data["@email"],
                "ref": data["@id_store"],
                "lat": data["@lat"],
                "lon": data["@lng"],
                "website": data["@link"],
            }

            yield Feature(**properties)
