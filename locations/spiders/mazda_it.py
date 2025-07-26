from locations.spiders.mazda_de import MazdaDESpider


class MazdaITSpider(MazdaDESpider):
    name = "mazda_it"
    allowed_domains = ["www.mazda.it"]
