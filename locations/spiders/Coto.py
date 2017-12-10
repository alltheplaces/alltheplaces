# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem


class CotoSpider(scrapy.Spider):
    name = "coto"
    allowed_domains = ["www.coto.com"]
    start_urls = ['http://www.coto.com.ar/mapassucursales/Sucursales/ListadoSucursalesPorDistancia.json.aspx?latitud=-34.6037389&longitud=-58.38157039999999&filtroComunidad=0&_=1512931386401']
    c_hours = 'Community Stand: '

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for data in results['results']:
            ref = data['id_suc']
            name = "Coto " + data['desc_suc']
            #  extras = data['DESC_TIPOSUC']
            street = data['direccion']
            phone = data['telefono']
            lat = data['latitud']
            lon = data['longitud']
            mon_thu = "Mo - Th : " + data['hor_lu_a_ju']
            fri = "Fr : " + data['hor_vi']
            sat = "Sa : " + data['hor_sa']
            sun = "Su : " + data['hor_do'] if data['hor_do'] != "Cerrado" else "Su : Closed"

            # Some stores also have community stand hours, var will use c_day
            if int(data['comunidadStand']) == 1:
                c_mon = "Mo : " + data['comunidadHor_LU']
                c_tue = "Tu : " + data['comunidadHor_MA']
                c_wed = "We : " + data['comunidadHor_MI']
                c_thu = "Th : " + data['comunidadHor_JU']
                c_fri = "Fr : " + data['comunidadHor_VI']
                c_sat = "Sa : " + data['comunidadHor_SA']
                c_sun = "Su : " + data['comunidadHor_DO']
                self.c_hours += "{}, {}, {}, {}, {}, {}, {}".format(
                    c_mon, c_tue, c_wed, c_thu, c_fri, c_sat, c_sun
                )


            yield GeojsonPointItem(
                ref=ref,
                lat=lat,
                lon=lon,
                #  extras=extras,
                name=name,
                street=street,
                country="Argentina",
                phone=phone,
                addr_full=street,
                opening_hours="{}, {}, {}, {} ".format(
                    mon_thu, fri, sat, sun).replace(' a ', ' - ') + (
                    self.c_hours if self.c_hours else ''
                )
            )

            self.c_hours = 'Community Stand: '
