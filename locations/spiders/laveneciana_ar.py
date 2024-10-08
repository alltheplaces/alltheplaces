import chompjs

from locations.json_blob_spider import JSONBlobSpider


class LavenecianaARSpider(JSONBlobSpider):
    name = "laveneciana_ar"
    item_attributes = {"brand": "La Veneciana"}
    allowed_domains = ["laveneciana.com.ar"]
    download_delay = 0.5
    start_urls = ("http://laveneciana.com.ar/sucursales/",)

    def extract_json(self, response):
        # var php_vars = {"markerIcon":"http:\/\/laveneciana.com.ar\/wp-content\/uploads\/2017\/09\/Pin_Logo_WhiteBorder-e1505163277731.png","sucursales":
        data = response.xpath('//script[contains(text(), "var php_vars =")]/text()').get().split("var php_vars = ")[1]
        return chompjs.parse_js_object(data)["sucursales"]

    def pre_process_data(self, location):
        # {'id': '31', 'nombre': 'Lomitas Street', 'direccion': 'Italia 459 | Lomas de Zamora | Buenos Aires', 'latitud': '-34.76602000', 'longitud': '-58.40212900', 'telefono': '7529 - 8791', 'email': '-', 'facebook': None, 'google_map_single': None, 'imagen': '800', 'filtro': 'buenosaires', 'wifi': '1', 'estacionamiento': '1', 'activo': '1'}
        location["nombre"] = location["nombre"].replace(" | ", ", ")
