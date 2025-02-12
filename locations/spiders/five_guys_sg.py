from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysSGSpider(FiveGuysAUSpider):
    name = "five_guys_sg"
    experience_key = "search-backend-sg"
    locale = "en-SG"
