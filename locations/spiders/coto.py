# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class CotoSpider(scrapy.Spider):
    name = "coto"
    item_attributes = {"brand": "Coto"}
    allowed_domains = ["www.coto.com"]
    start_urls = [
        "http://www.coto.com.ar/mapassucursales/Sucursales/ListadoSucursalesPorDistancia.json.aspx?latitud=-34.6037389&longitud=-58.38157039999999&filtroComunidad=0&_=1512931386401"
    ]

    def parse(self, response):
        results = response.json()
        for data in results["results"]:
            ref = data["id_suc"]
            name = "Coto " + data["desc_suc"]
            street = data["direccion"]
            phone = data["telefono"]
            lat = data["latitud"]
            lon = data["longitud"]
            mon_thu = "Mo-Th " + data["hor_lu_a_ju"]
            fri = "Fr " + data["hor_vi"]
            sat = "Sa " + data["hor_sa"]
            sun = "Su " + data["hor_do"] if data["hor_do"] != "Cerrado" else "Su off"
            opening_hours = "{}; {}; {}; {}".format(mon_thu, fri, sat, sun).replace(
                " a ", "-"
            )

            yield GeojsonPointItem(
                ref=ref,
                lat=lat,
                lon=lon,
                name=name,
                street=street,
                country="Argentina",
                phone=phone,
                addr_full=street,
                opening_hours=opening_hours,
            )
