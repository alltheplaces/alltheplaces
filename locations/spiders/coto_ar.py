import scrapy

from locations.items import Feature


class CotoARSpider(scrapy.Spider):
    name = "coto_ar"
    item_attributes = {"brand": "Coto", "brand_wikidata": "Q5175411"}
    start_urls = ["https://www.coto.com.ar/sucursales/index.asp"]

    def parse(self, response, **kwargs):
        for store in response.xpath("//tbody/tr"):
            item = Feature()
            item["name"] = self.item_attributes["brand"]
            item["branch"] = store.xpath('.//*[@data-label="Barrio"]/text()').get()
            item["street_address"] = store.xpath('.//*[@data-label="Direccion"]/text()').get()
            item["phone"] = store.xpath('.//*[@data-label="Telefono"]/text()').get()
            item["ref"] = store.xpath('.//*[@data-label="Suc"]/text()').get()
            yield item
