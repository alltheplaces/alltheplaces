from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysDESpider(FiveGuysAUSpider):
    name = "five_guys_de"
    api_key = "8305fbf269956ad9f4ebacaa7363a875"
    experience_key = "search-backend-de"
    locale = "de"
