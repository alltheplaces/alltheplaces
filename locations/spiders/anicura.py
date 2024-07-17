from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class AnicuraSpider(SitemapSpider, StructuredDataSpider):
    name = "anicura"
    item_attributes = {"brand": "AniCura", "brand_wikidata": "Q21100245", "extras": Categories.VETERINARY.value}
    sitemap_urls = [
        "https://www.anicura.at/robots.txt",
        "https://www.anicura.be/robots.txt",
        "https://www.anicura.dk/robots.txt",
        "https://www.anicura.fr/robots.txt",
        "https://www.anicura.de/robots.txt",
        "https://www.anicura.it/robots.txt",
        "https://www.anicura.no/robots.txt",
        "https://www.anicura.pt/robots.txt",
        "https://www.anicura.es/robots.txt",
        "https://www.anicura.se/robots.txt",
        "https://www.anicura.ch/robots.txt",
        "https://www.anicura.nl/robots.txt",
        "https://www.anicura.pl/robots.txt",
    ]
    sitemap_rules = [
        (r"at/standorte/[^/]+/$", "parse"),
        (r"be/klinieken/[^/]+/[^/]+/$", "parse"),
        (r"dk/klinikker/[^/]+/$", "parse"),
        (r"fr/cliniques/[^/]+/$", "parse"),
        (r"de/standorte/[^/]+/$", "parse"),
        (r"it/cliniche/[^/]+/$", "parse"),
        (r"no/klinikker/[^/]+/$", "parse"),
        (r"pt/clinicas-veterinarias/[^/]+/$", "parse"),
        (r"es/clinicas/[^/]+/$", "parse"),
        (r"se/hitta-klinik/[^/]+/$", "parse"),
        (r"ch/standorte/[^/]+/$", "parse"),
        (r"nl/klinieken/[^/]+/[^/]+/$", "parse"),
        (r"pl/clinicas-veterinarias/[^/]+/$", "parse"),
    ]
    wanted_types = ["VeterinaryCare"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("AniCura ")
        extract_google_position(item, response)

        yield item
