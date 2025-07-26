from locations.spiders.mazda_de import MazdaDESpider


class MazdaHRSpider(MazdaDESpider):
    name = "mazda_hr"
    allowed_domains = ["www.mazda.hr"]
