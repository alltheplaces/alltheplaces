from locations.spiders.mazda_de import MazdaDESpider


class MazdaCZSpider(MazdaDESpider):
    name = "mazda_cz"
    allowed_domains = ["www.mazda.cz"]
