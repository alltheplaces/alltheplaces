import json
import scrapy
from locations.items import GeojsonPointItem

class DiscoArgentinaSpider(scrapy.Spider):
    name = "disco_argentina"
    allowed_domains = ["www.disco.com.ar"]

    def start_requests(self):
        url = 'https://www.disco.com.ar/Login/PreHomeService.aspx/TraerLocales'
        headers={
                    'Content-Type': 'application/json',
                }
        form_data = {}

        yield scrapy.http.FormRequest(
            url=url, method='POST', formdata=form_data,
            headers=headers, callback=self.parse
        )

    def parse(self, response):
        result = response.body_as_unicode().replace("\\", '')
        result = result.replace("{\"d\":\"", '')
        result = result[:-2]
        data = json.loads(result)
        for store in data['Locales']:
            properties = {
                'ref': store['Local']['IdProvincia'].strip(),
                'name': store['Local']['Nombre'].strip(),
                'addr_full': store['Local']['Direccion'].strip(),
                'city': store['Local']['Localidad'].strip(),
                'state': store['Local']['Provincia'].strip(),
                'postcode': store['Local']['CodigoPostal'].strip(),
                'lat': store['Local']['Latitud'].strip(),
                'lon': store['Local']['Longitud'].strip(),
                'phone': store['Local']['Telefono'].strip(),
            }

            yield GeojsonPointItem(**properties)