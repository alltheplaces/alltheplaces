from locations.spiders.mazda_de import MazdaDESpider


class MazdaPTSpider(MazdaDESpider):
    name = "mazda_pt"
    allowed_domains = ["www.mazda.pt"]
