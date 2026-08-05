import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

MEDIAMARKT = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}
MEDIAWORLD = {"brand": "MediaWorld", "brand_wikidata": "Q125054068"}
SATURN = {"brand": "Saturn", "brand_wikidata": "Q2543504"}


class MediamarktSpider(SitemapSpider, StructuredDataSpider):
    name = "mediamarkt"
    requires_proxy = True
    allowed_domains = [
        "www.mediamarkt.at",
        "www.mediamarkt.be",
        "www.mediamarkt.ch",
        "www.mediamarkt.de",
        "www.mediamarkt.es",
        "www.mediamarkt.hu",
        "www.mediamarkt.nl",
        "www.mediaworld.it",
        "mediamarkt.pl",
        "www.saturn.de",
    ]
    sitemap_urls = [
        "https://www.mediamarkt.at/sitemaps/sitemap-marketpages.xml",
        "https://www.mediamarkt.be/sitemaps/fr/sitemap-marketpages.xml",
        "https://www.mediamarkt.ch/sitemaps/fr/sitemap-marketpages.xml",
        "https://www.mediamarkt.de/sitemaps/sitemap-marketpages.xml",
        "https://www.mediamarkt.es/sitemaps/sitemap-marketpages.xml",
        "https://www.mediamarkt.hu/sitemaps/sitemap-marketpages.xml",
        "https://www.mediamarkt.nl/sitemaps/sitemap-marketpages.xml",
        "https://www.mediaworld.it/sitemaps/sitemap-marketpages.xml",
        "https://www.saturn.de/sitemaps/sitemap-marketpages.xml",
        "https://mediamarkt.pl/sitemaps/sitemap-marketpages.xml",
    ]
    sitemap_rules = [("/store/", "parse_sd")]

    brands = {
        "www.mediamarkt.at": MEDIAMARKT,
        "www.mediamarkt.be": MEDIAMARKT,
        "www.mediamarkt.ch": MEDIAMARKT,
        "www.mediamarkt.de": MEDIAMARKT,
        "www.mediamarkt.es": MEDIAMARKT,
        "www.mediamarkt.hu": MEDIAMARKT,
        "www.mediamarkt.nl": MEDIAMARKT,
        "www.mediaworld.it": MEDIAWORLD,
        "mediamarkt.pl": MEDIAMARKT,
        "www.saturn.de": SATURN,
    }

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.split("/")[-1]
        host = response.url.split("/")[2]
        item.update(self.brands[host])
        item["branch"] = item.pop("name", "").replace(f"{item['brand']} ", "")
        item["name"] = item["brand"]
        if phone := item.get("phone"):
            item["phone"] = re.sub(r"[^0-9+]", "", phone)
        apply_category(Categories.SHOP_ELECTRONICS, item)
        yield item
