from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysBHSpider(FiveGuysAUSpider):
    name = "five_guys_bh"
    experience_key = "search-backend-bh"
    locale = "ar-BH"
