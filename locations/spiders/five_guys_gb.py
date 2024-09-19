from locations.spiders.five_guys_au import FiveGuysAUSpider


class FiveGuysGBSpider(FiveGuysAUSpider):
    name = "five_guys_gb"
    api_key = "8305fbf269956ad9f4ebacaa7363a875"
    experience_key = "search-backend"
