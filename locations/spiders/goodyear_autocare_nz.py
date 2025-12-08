from locations.spiders.goodyear_autocare_au import GoodyearAutocareAUSpider


class GoodyearAutocareNZSpider(GoodyearAutocareAUSpider):
    name = "goodyear_autocare_nz"
    allowed_domains = ["www.goodyear.co.nz"]
    sitemap_urls = ["https://www.goodyear.co.nz/store-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.goodyear\.co\.nz\/store-locator\/goodyear-autocare-[\w\-]+$", "parse")]
