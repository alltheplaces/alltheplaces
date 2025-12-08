from locations.spiders.paul_ro import PaulROSpider


class PaulGASpider(PaulROSpider):
    name = "paul_ga"
    start_urls = ["http://www.paul-gabon.com/en/our-shops?ajax=1&all=1"]
    country = "GA"
