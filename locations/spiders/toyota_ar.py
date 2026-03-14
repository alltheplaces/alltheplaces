from locations.spiders.toyota_br import ToyotaBRSpider


class ToyotaARSpider(ToyotaBRSpider):
    name = "toyota_ar"
    start_urls = ["https://www.toyota.com.ar/encontra-tu-concesionario-toyota"]
