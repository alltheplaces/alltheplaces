from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysIESpider(FiveGuysAUSpider):
    name = "five_guys_ie"
    experience_key = "search-backend-ie"
    locale = "en-IE"
