from locations.spiders.mazda_de import MazdaDESpider


class MazdaSESpider(MazdaDESpider):
    name = "mazda_se"
    allowed_domains = ["www.mazda.se"]
