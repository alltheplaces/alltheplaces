from locations.spiders.five_guys_ca import FiveGuysCASpider


class FiveGuysUSSpider(FiveGuysCASpider):
    name = "five_guys_us"
    item_attributes = {
        "brand": "Five Guys",
        "brand_wikidata": "Q1131810",
    }
    sitemap_urls = ["https://restaurants.fiveguys.com/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.com\/[^/]+$", "parse_sd")]
