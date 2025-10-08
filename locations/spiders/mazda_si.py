from locations.spiders.mazda_de import MazdaDESpider


class MazdaSISpider(MazdaDESpider):
    name = "mazda_si"
    allowed_domains = ["www.mazda.si"]
