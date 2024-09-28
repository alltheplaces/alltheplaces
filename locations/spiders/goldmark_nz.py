from locations.spiders.goldmark_au import GoldmarkAUSpider


class GoldmarkNZSpider(GoldmarkAUSpider):
    name = "goldmark_nz"
    allowed_domains = ["www.goldmark.co.nz"]
    start_urls = ["https://www.goldmark.co.nz/stores/all-stores"]
