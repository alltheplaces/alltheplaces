from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AlbertsonsSpider(SitemapSpider, StructuredDataSpider):
    name = "albertsons"
    brands = {
        "albertsons": {"brand": "Albertsons", "brand_wikidata": "Q2831861"},
        "acmemarkets": {"brand": "ACME Markets", "brand_wikidata": "Q341975"},
        "albertsonsmarket": {
            "brand": "Albertsons Market",
            "brand_wikidata": "Q115350320",
        },
        "amigosunited": {"brand": "Amigos", "brand_wikidata": "Q115350331"},
        "andronicos": {"brand": "Andronico's", "brand_wikidata": "Q4759491"},
        "carrsqc": {"brand": "Carrs", "brand_wikidata": "Q5046735"},
        "jewelosco": {"brand": "Jewel-Osco", "brand_wikidata": "Q3178470"},
        "kingsfoodmarkets": {"brand": "Kings", "brand_wikidata": "Q6412914"},
        "luckylowprices": {"brand": "Lucky", "brand_wikidata": "Q6698032"},
        "marketstreetunited": {
            "brand": "Market Street",
            "brand_wikidata": "Q119405196",
        },
        "pavilions": {"brand": "Pavilions", "brand_wikidata": "Q7155886"},
        "randalls": {"brand": "Randalls", "brand_wikidata": "Q7291489"},
        "shaws": {"brand": "Shaw's", "brand_wikidata": "Q578387"},
        "starmarket": {"brand": "Star Market", "brand_wikidata": "Q7600795"},
        "tomthumb": {"brand": "Tom Thumb", "brand_wikidata": "Q7817826"},
        "unitedsupermarkets": {
            "brand": "United Supermarkets",
            "brand_wikidata": "Q17108901",
        },
        "vons": {"brand": "Vons", "brand_wikidata": "Q7941609"},
    }
    item_attributes = {"nsi_id": "-1"}  # Most of these are too small to justify NSI entries
    allowed_domains = [
        "local.albertsons.com",
        "local.fuel.albertsons.com",
        "local.pharmacy.albertsons.com",
        "local.acmemarkets.com",
        "local.fuel.acmemarkets.com",
        "local.pharmacy.acmemarkets.com",
        "local.albertsonsmarket.com",
        "local.pharmacy.albertsonsmarket.com",
        "local.amigosunited.com",
        "local.pharmacy.amigosunited.com",
        "local.andronicos.com",
        "local.carrsqc.com",
        "local.fuel.carrsqc.com",
        "local.pharmacy.carrsqc.com",
        "local.jewelosco.com",
        "local.fuel.jewelosco.com",
        "local.pharmacy.jewelosco.com",
        "local.kingsfoodmarkets.com",
        "local.luckylowprices.com",
        "local.pharmacy.luckylowprices.com",
        "local.marketstreetunited.com",
        "local.pharmacy.marketstreetunited.com",
        "local.pavilions.com",
        "local.pharmacy.pavilions.com",
        "local.randalls.com",
        "local.fuel.randalls.com",
        "local.pharmacy.randalls.com",
        "local.shaws.com",
        "local.pharmacy.shaws.com",
        "local.starmarket.com",
        "local.pharmacy.starmarket.com",
        "local.tomthumb.com",
        "local.fuel.tomthumb.com",
        "local.pharmacy.tomthumb.com",
        "local.unitedsupermarkets.com",
        "local.pharmacy.unitedsupermarkets.com",
        "local.vons.com",
        "local.fuel.vons.com",
        "local.pharmacy.vons.com",
    ]
    sitemap_urls = [f"https://{domain}/robots.txt" for domain in allowed_domains]
    sitemap_rules = [
        (
            r"https://local\.(?:fuel\.|pharmacy\.)?\w+\.com/\w\w/[-\w]+/[-\w]+\.html$",
            "parse_sd",
        )
    ]
    wanted_types = ["GroceryStore", "GasStation", "Pharmacy"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if ld_data["@type"] == "GroceryStore":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif ld_data["@type"] == "GasStation":
            apply_category(Categories.FUEL_STATION, item)
        elif ld_data["@type"] == "Pharmacy":
            apply_category(Categories.PHARMACY, item)

        item.update(self.brands[response.url.split("/")[2].split(".")[-2]])

        # Remove fields that are not specific to individual stores.
        item.pop("facebook", None)
        item.pop("twitter", None)

        yield item
