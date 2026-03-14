from locations.spiders.mazda_de import MazdaDESpider


class MazdaATSpider(MazdaDESpider):
    name = "mazda_at"
    allowed_domains = ["www.mazda.at"]
