from locations.spiders.mazda_de import MazdaDESpider


class MazdaESSpider(MazdaDESpider):
    name = "mazda_es"
    allowed_domains = ["www.mazda.es"]
