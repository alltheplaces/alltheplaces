import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HondaSpider(SitemapSpider, StructuredDataSpider):
    name = "honda"
    item_attributes = {"brand": "Honda", "brand_wikidata": "Q9584"}
    sitemap_urls = [
        "https://www.honda.de/sitemap.xml",
        "https://www.honda.it/sitemap.xml",
        "https://auto.honda.fr/cars/sitemap.xml",
        "https://www.honda.es/sitemap.xml",
        "https://www.honda.nl/sitemap.xml",
        "https://www.honda.at/sitemap.xml",
        "https://www.honda.hu/sitemap.xml",
        "https://www.honda.co.uk/sitemap.xml",
        "https://www.honda.pl/sitemap.xml",
        "https://www.fr.honda.be/sitemap.xml",
        "https://www.honda.no/sitemap.xml",
        "https://www.honda.cz/sitemap.xml",
        "https://www.honda.dk/sitemap.xml",
        "https://www.de.honda.ch/sitemap.xml",
        "https://www.honda.se/sitemap.xml",
    ]
    sitemap_follow = ["/cars/", "/motorcycles/"]
    sitemap_rules = [
        ("/dealers/", "parse_sd"),
        ("/concessionarie/", "parse_sd"),
        ("/concessionarios/", "parse_sd"),
        ("/concesionarios/", "parse_sd"),
        ("/handler/", "parse_sd"),
        ("/concessionnaires/", "parse_sd"),
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("industrie", "auto")
            yield entry

    def post_process_item(self, item, response, ld_data, **kwargs):
        if isinstance(item["email"], list):
            item["email"] = item["email"][0]
        item_name = response.xpath('//*[@class="dealer-name"]/h1/text()').get()
        item["name"] = item_name if item_name is not None else "Honda"
        if street_address := item.get("street_address"):
            item["street_address"] = street_address.strip()
        coords_url = response.xpath('//*[@class="dealer-map"]/a/@href').get()
        if coords := re.search(r"@(-?\d+.\d+),\s?(-?\d+.\d+)", coords_url):
            item["lat"] = coords.group(1)
            item["lon"] = coords.group(2)
        if response.url.endswith("service.html") or "service" in item["name"]:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        elif "/motorcycles/" in response.url:
            apply_category(Categories.SHOP_MOTORCYCLE, item)
        else:
            apply_category(Categories.SHOP_CAR, item)
        yield item
