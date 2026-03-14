from locations.spiders.albert_heijn_nl import AlbertHeijnNLSpider


class AlbertHeijnBESpider(AlbertHeijnNLSpider):
    name = "albert_heijn_be"
    allowed_domains = ["www.ah.be"]
    start_urls = ["https://www.ah.be/winkels"]
