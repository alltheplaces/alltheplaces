from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_ES, OpeningHours


class PlazaVeaPESpider(Spider):
    name = "plaza_vea_pe"
    item_attributes = {"brand": "Plaza Vea", "brand_wikidata": "Q7203672"}
    start_urls = ["https://vea.plazavea.com.pe/controller.aspx?ope=tiendas&p1=14&p2=-1&p3=-1"]

    def parse(self, response):
        for location in response.json():
            # This doesn't pick up much at the moment, but I'm assuming it may turn multi lingual down the track
            item = DictParser.parse(location)
            item["ref"] = location["TIE_CODIGO"]
            item["name"] = location["TIE_NOMBRE"]
            item["lon"] = location["TIE_GMAP_LONGITUD"]
            item["lat"] = location["TIE_GMAP_LATITUD"]
            item["phone"] = location["TIE_TELEFONO"]
            item["street_address"] = location["TIE_DIRECCION"]
            item["opening_hours"] = OpeningHours()

            # 'TIE_HORARIO': 'L-D 08:00 - 22:00 hrs. '
            cleaned_hours = location["TIE_HORARIO"].replace("L", "Lunes").replace("D", "Domingo")
            item["opening_hours"].add_ranges_from_string(cleaned_hours, DAYS_ES)

            # Some locations include services:
            # "TIE_SERVICIOS": "Banco Interbank, Farmacia Inkafarma y óptica Econolentes",

            yield item
