import scrapy

from locations.items import Feature


class VeaSpider(scrapy.Spider):
    name = "vea"
    item_attributes = {"brand": "Vea Cencosud"}
    allowed_domains = ["www.supermercadosvea.com"]
    start_urls = ("http://www.supermercadosvea.com.ar/sucursales-obtener.html",)
    requires_proxy = True

    def parse(self, response):
        store_list = response.json()
        for store in store_list:
            properties = {
                "name": store["descripcion"],
                "addr_full": store["direccion"],
                "city": store["vea_localidades_desc"],
                "opening_hours": store["horarios"],
                "phone": store["telefonos"],
                "ref": str(store["codigo"]).replace("SM ", ""),
            }
            yield Feature(**properties)
