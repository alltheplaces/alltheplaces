import json

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
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
    drop_attributes = {"facebook", "image", "twitter"}
    search_for_email = False
    search_for_image = False
    custom_settings = {
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        # "DOWNLOAD_DELAY": 0.25,  # This can safely be set to 0.25 for local runs.
    }

    def pre_process_data(self, ld_data, **kwargs):
        ld_data.pop("openingHours", None)
        ld_data.pop("openingHoursSpecification", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        if store_id := response.xpath("//*[@data-entity-id]/@data-entity-id").get():
            item["ref"] = store_id

        if raw_days := response.xpath("//@data-days").get():
            oh = OpeningHours()
            for day in json.loads(raw_days):
                if day.get("isClosed"):
                    oh.set_closed(day["day"])
                    continue
                for interval in day.get("intervals", []):
                    oh.add_range(
                        day=day.get("day"),
                        open_time=f"{interval['start']:04d}",
                        close_time=f"{interval['end']:04d}",
                        time_format="%H%M",
                    )
            item["opening_hours"] = oh

        if ld_data["@type"] == "GroceryStore":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif ld_data["@type"] == "GasStation":
            apply_category(Categories.FUEL_STATION, item)
        elif ld_data["@type"] == "Pharmacy":
            apply_category(Categories.PHARMACY, item)

        item.update(self.brands[response.url.split("/")[2].split(".")[-2]])

        yield item
