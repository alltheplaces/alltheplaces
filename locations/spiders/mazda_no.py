from locations.spiders.mazda_de import MazdaDESpider


class MazdaNOSpider(MazdaDESpider):
    name = "mazda_no"
    allowed_domains = ["www.mazda.no"]
