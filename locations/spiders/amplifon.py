import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AmplifonSpider(SitemapSpider, StructuredDataSpider):
    name = "amplifon"
    BRANDS = {
        "amplifon": ("Amplifon", "Q477222"),
        "beterhoren": ("Beter Horen", "Q98282942"),
        "bayaudiology": ("Bay Audiology", "Q24189803"),
        "gaes": ("GAES", "Q98492565"),
        "minisom": ("Minisom", ""),
    }
    sitemap_urls = [
        "https://www.amplifon.com/fr/sitemap_store.xml",
        "https://www.amplifon.com/it/sitemap_store.xml",
        "https://www.amplifon.com/nl-be/sitemap_store.xml",
        "https://www.amplifon.com/de/sitemap_store.xml",
        "https://www.amplifon.com/hu/sitemap_store.xml",
        "https://www.amplifon.com/pl/sitemap_store.xml",
        "https://www.amplifon.com/de-ch/sitemap_store.xml",
        "https://www.amplifon.com/uk/sitemap_store.xml",
        "https://www.amplifon.com/in/sitemap_store.xml",
        "https://www.amplifon.com/au/sitemap_store.xml",
        "https://www.beterhoren.nl/sitemap_store.xml",
        "https://www.bayaudiology.co.nz/sitemap_store.xml",
        "https://www.gaesargentina.com.ar/entidades.xml",
        "https://www.gaes.cl/entidades.xml",
        "https://www.gaes.co/entidades.xml",
        "https://www.gaes.ec/entidades.xml",
        "https://www.gaes.es/sitemap_store.xml",
        "https://www.minisom.pt/sitemap_store.xml",
    ]
    sitemap_rules = [
        (r"https://www.amplifon.com/[-\w]+/[-\w]+/[-\w]+/[-\w]+", "parse_sd"),
        (r"https://www.beterhoren.nl/audiciens/[-\w]+/[-\w]+", "parse_sd"),
        (r"https://www.bayaudiology.co.nz/store-locator/[-\w]+/[-\w]+", "parse_sd"),
        (r"https://www.gaesargentina.com.ar/localizador-centros-auditivos-gaes/[-\w]+", "parse_sd"),
        (r"https://www.gaes.\w{2}/localizador-centros-auditivos-gaes/[-\w]+", "parse_sd"),
        (r"https://www.gaes.es/nuestros-centros-auditivos/[-\w]+/[-\w]+", "parse_sd"),
        (r"https://www.minisom.pt/centros-minisom/[-\w]+/[-\w]+", "parse_sd"),
    ]
    wanted_types = ["MedicalBusiness", "LocalBusiness"]
    custom_settings = {"REDIRECT_ENABLED": "False"}  # avoid redirects to locations list
    coordinates_pattern = re.compile(r"LatLng\((-?[.\d]+)[,\s]+(-?[.\d]+)\)")

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("image") in (
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/outside/de/FG%2520Hellersdorf-2.jpg",
            "https://www.amplifon.com/content/dam/amplifon-emea/stores/it/store.png",
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/inside/fr/397_2018-02-22-14-52-49_1.JPG",
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/inside/ch/Luzern-Hirschmatt-Empfang.jpg",
            "https://assets-apac.amplifon.com/content/dam/content-factory-nz/store/unbranded/_DSC9556.jpg",
            "https://www.minisom.pt/content/dam/content-factory/photos/Store/inside/pt/PT%20inside%20Store.jpg",
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/shooting/amplicare-new-store-concept/goodbye-man-no-coat-minisom.jpg",
            "https://www.beterhoren.nl/content/dam/content-factory/photos/tvc-campaign/nl/netherlands/tvc_beterhoren2.jpg",
            "https://assets-apac.amplifon.com/content/dam/content-factory/photos/Store/shooting/amplifon/amplifon-941.jpg",
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/inside/fr/amplifon_store_interior_3.jpg",
            "https://assets-apac.amplifon.com/content/dam/amplifon-apac/au/amplicare-amplifon/outside-store/couple_male_grey_female_blonde_leave_store_horizontal_v2.jpg",
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/outside/de/FG%20Hellersdorf-2.jpg",
            "https://www.gaes.es/content/dam/content-factory/photos/Store/outside/es/_LimboAgency_Gaes_190611_0043.jpg",
            "https://www.amplifon.com/content/dam/content-factory/photos/Store/shooting/amplicare-new-store-concept/audiologist-female-portrait-coat.jpg",
            "https://www.amplifon.com/content/dam/content-factory/photos/amplifon-hq/2019-07-16-AMPLIFON%20Azienda%200039.jpg",
        ):
            item["image"] = None

        if not item.get("lat"):
            if coordinates := re.search(self.coordinates_pattern, response.text):
                item["lat"], item["lon"] = coordinates.groups()
        item["phone"] = (
            item["phone"].replace("%20", " ").replace("(", "").replace(")", "") if item.get("phone") else None
        )
        brand = response.url.split(".")[1].replace("gaesargentina", "gaes")
        if brand_details := self.BRANDS.get(brand):
            item["brand"], item["brand_wikidata"] = brand_details
        if item["brand"].title() not in item["name"].title():  # Skip third party shop
            return
        item["branch"] = item.pop("name").replace("Amplifon ", "")
        apply_category(Categories.SHOP_HEARING_AIDS, item)
        yield item
