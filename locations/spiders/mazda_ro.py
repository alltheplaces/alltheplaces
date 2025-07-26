from locations.spiders.mazda_de import MazdaDESpider


class MazdaROSpider(MazdaDESpider):
    name = "mazda_ro"
    allowed_domains = ["www.mazda.ro"]
