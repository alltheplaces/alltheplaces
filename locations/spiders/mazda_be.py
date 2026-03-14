from locations.spiders.mazda_de import MazdaDESpider


class MazdaBESpider(MazdaDESpider):
    name = "mazda_be"
    allowed_domains = ["fr.mazda.be"]
