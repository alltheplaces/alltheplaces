from locations.spiders.toyota_br import ToyotaBRSpider


class ToyotaVESpider(ToyotaBRSpider):
    name = "toyota_ve"
    start_urls = ["https://www.toyota.com.ve/encuentra-tu-concesionario-toyota"]
