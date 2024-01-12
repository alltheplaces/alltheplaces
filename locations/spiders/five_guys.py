from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


# For countries DE, ES, FR and GB: refer to separate FiveGuysYextSpider.
class FiveGuysSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys"
    item_attributes = {
        "brand": "Five Guys",
        "brand_wikidata": "Q1131810",
    }
    sitemap_urls = [
        "https://restaurants.fiveguys.com/sitemap.xml",
        "https://restaurants.fiveguys.ae/sitemap.xml",
        "https://restaurants.fiveguys.at/sitemap.xml",
        "https://restaurants.fiveguys.com.au/sitemap.xml",
        "https://restaurants.fiveguys.be/sitemap.xml",
        "https://restaurants.fiveguys.bh/sitemap.xml",
        "https://restaurants.fiveguys.ca/sitemap.xml",
        "https://restaurants.fiveguys.ch/sitemap.xml",
        "https://restaurants.fiveguys.cn/sitemap.xml",
        # "https://restaurants.fiveguys.de/sitemap.xml",
        # "https://restaurantes.fiveguys.es/sitemap.xml",
        # "https://restaurants.fiveguys.fr/sitemap.xml",
        "https://restaurants.fiveguys.com.hk/sitemap.xml",
        "https://restaurants.fiveguys.ie/sitemap.xml",
        "https://restaurants.fiveguys.co.kr/sitemap.xml",
        "https://restaurants.fiveguys.com.kw/sitemap.xml",
        "https://restaurants.fiveguys.it/sitemap.xml",
        "https://restaurants.fiveguys.lu/sitemap.xml",
        "https://restaurants.fiveguys.mo/sitemap.xml",
        "https://restaurants.fiveguys.my/sitemap.xml",
        "https://restaurants.fiveguys.nl/sitemap.xml",
        "https://restaurants.fiveguys.qa/sitemap.xml",
        "https://restaurants.fiveguys.sa/sitemap.xml",
        "https://restaurants.fiveguys.sg/sitemap.xml",
        # "https://restaurants.fiveguys.co.uk/sitemap.xml",
    ]
    sitemap_rules = [
        (r"^https://restaurants\.fiveguys\.com\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.ae\/en_ae\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.at\/en_at\/(?!search$)[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.com\.au\/(?!(index\.html$|search$))[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.be\/en_be\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.bh\/en_bh\/(?!search$)[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.ca\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.ch\/en_ch\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.cn\/en\/[^/]+$", "parse_sd"),
        # (r"^https://restaurants\.fiveguys\.de\/[^/]+\/[^/]+$", "parse_sd"),
        # (r"^https://restaurants\.fiveguys\.es\/[^/]+\/[^/]+$", "parse_sd"),
        # (r"^https://restaurants\.fiveguys\.fr\/[^/]+\/[^/]+$", "parse_sd"),
        ("^https://restaurants\.fiveguys\.com\.hk\/en_hk\/(?!search$)[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.ie\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.co\.kr\/en\/(?!search$)[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.com\.kw\/en_kw\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.it\/en_it\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.lu\/en_lu\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.mo\/en\/(?!search$)[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.my\/en\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.nl\/en_nl\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.qa\/en_qa\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.sa\/en_sa\/[^/]+$", "parse_sd"),
        (r"^https://restaurants\.fiveguys\.sg\/[^/]+$", "parse_sd"),
        # (r"^https://restaurants\.fiveguys\.co\.uk\/.+$", "parse_sd"),
    ]
    download_delay = 0.5
