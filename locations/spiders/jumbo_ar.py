import json

import scrapy

from locations.items import Feature


class JumboARSpider(scrapy.Spider):
    name = "jumbo_argentina"
    item_attributes = {"brand": "Jumbo"}
    allowed_domains = ["www.jumbo.com.ar"]

    def start_requests(self):
        url = "https://www.jumbo.com.ar/Login/PreHomeService.aspx/TraerLocales"
        headers = {
            "Content-Type": "application/json",
        }
        form_data = {}

        yield scrapy.http.FormRequest(
            url=url,
            method="POST",
            formdata=form_data,
            headers=headers,
            callback=self.parse,
        )

    def parse(self, response):
        result = response.text.replace("\\", "")
        result = result[:5] + result[6:-2] + result[-1:]
        data = json.loads(result)
        ref = 0
        for store in data["d"]["Locales"]:
            properties = {
                "ref": ref,
                "name": store["Local"]["Nombre"].strip(),
                "addr_full": store["Local"]["Direccion"].strip(),
                "city": store["Local"]["Localidad"].strip(),
                "state": store["Local"]["Provincia"].strip(),
                "postcode": store["Local"]["CodigoPostal"].strip(),
                "lat": float(store["Local"]["Latitud"].strip()),
                "lon": float(store["Local"]["Longitud"].strip()),
                "phone": store["Local"]["Telefono"].strip(),
            }
            ref += 1
            yield Feature(**properties)
