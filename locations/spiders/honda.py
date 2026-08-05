import re
from copy import deepcopy

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider

SALE_DEPARTMENT = re.compile(
    r"\b(?:sales|motorrad|motorräder|motoren|motocross|motorfietsen|motos|scooters|salg"
    r"|verkauf|verkoop|vendita|vendas|venda|ventas|vente"
    r"|ventes|händler|venta|prodej|predaj|sprzedaż|försäljning|értékesítés)\b",
    re.IGNORECASE,
)

SERVICE_DEPARTMENT = re.compile(
    r"\b(?:service|services|servicing|servicio|servis|serwis|szerviz|kundendienst"
    r"|kundenservice|assistenza|assistência|entretien|réparation|posventa)\b",
    re.IGNORECASE,
)


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
        "https://www.honda.sk/sitemap.xml",
        "https://www.honda.lu/sitemap.xml",
        "https://www.honda.pt/sitemap.xml",
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
        item["country"] = response.xpath("//html/@country").get()
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
        departments = response.css("section.fad-dealer-services-wrapper h2::text").getall()
        is_sale = any(SALE_DEPARTMENT.search(department) for department in departments)
        is_service = any(SERVICE_DEPARTMENT.search(department) for department in departments)
        is_service = is_service or "taller" in item["name"].lower()

        if not is_sale and not is_service:
            self.logger.warning(
                f"Unknown departments (defaulting to shop=car / motorcycle): {departments} - {response.url}"
            )
            is_sale = True

        if is_service:
            yield self.build_service_item(item, response)
        if is_sale:
            yield self.build_sales_item(item, response)

    def build_sales_item(self, item, response):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-SALES"
        if "/motorcycles/" in response.url:
            apply_category(Categories.SHOP_MOTORCYCLE, sales_item)
        else:
            apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item, response):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-SERVICE"
        if "/motorcycles/" in response.url:
            apply_category(Categories.SHOP_MOTORCYCLE_REPAIR, service_item)
        else:
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item
