from locations.spiders.mazda_de import MazdaDESpider


class MazdaIESpider(MazdaDESpider):
    name = "mazda_ie"
    allowed_domains = ["www.mazda.ie"]
