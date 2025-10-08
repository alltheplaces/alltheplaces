import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, FuelCards, PaymentMethods, apply_category, apply_yes_no
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import extract_phone


class BenzaITSpider(SitemapSpider):
    name = "benza_it"
    allowed_domains = ["www.b-benza.it"]
    sitemap_urls = ["https://www.b-benza.it/sitemap_index.xml"]
    sitemap_rules = [("/services/.+", "parse_station")]
    item_attributes = {"brand": "Benza", "brand_wikidata": "Q131781765"}

    def parse_station(self, response):
        item = Feature()
        item["ref"] = response.url.strip("/").split("/")[-1]
        item["website"] = response.url
        article = response.css("article")
        item["image"] = article.css("img::attr(src)").get()
        extract_google_position(item, response)
        extract_phone(item, article)
        apply_category(Categories.FUEL_STATION, item)
        item["name"] = "Benza"
        item["addr_full"] = addr = [s.strip() for s in article.xpath("//p[2]/text()").getall()]
        item["branch"] = addr[0]
        item["street_address"] = addr[1]
        if match := re.match(r"(\d+)\s*([\w ]+)(?:\s*\((\w+)\))?", addr[2]):
            item["postcode"], item["city"], item["state"] = match.groups()
        for service in [s.strip().lower() for s in article.css("ul li::text").getall()]:
            apply_yes_no(Fuel.OCTANE_95, item, "benzina" in service)
            apply_yes_no(Fuel.LPG, item, "gpl" in service)
            apply_yes_no(Fuel.DIESEL, item, "gasolio" in service)
            apply_yes_no(Fuel.ADBLUE, item, "adblue" in service)
            apply_yes_no("car_wash", item, "wash" in service)
            apply_yes_no(PaymentMethods.CASH, item, ("contanti" in service) or ("contante" in service))
            apply_yes_no(
                PaymentMethods.CARDS, item, ("carte di credito" in service) or ("carta di credito" in service)
            )  # "credit cards" means any card actually
            apply_yes_no(PaymentMethods.BANCOMAT, item, ("bancomat" in service))
            apply_yes_no(PaymentMethods.SATISPAY, item, ("satispay" in service))
            apply_yes_no(FuelCards.UTA, item, ("uta" in service))
            apply_yes_no(FuelCards.DKV, item, ("dkv" in service))
            apply_yes_no("fuel:discount", item, True)
            apply_yes_no("self_service", item, True)
            apply_yes_no("full_service", item, "service 24h" in service)
        return item
