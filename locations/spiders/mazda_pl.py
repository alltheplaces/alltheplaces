from locations.spiders.mazda_de import MazdaDESpider


class MazdaPLSpider(MazdaDESpider):
    name = "mazda_pl"
    allowed_domains = ["www.mazda.pl"]
