import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class WindtreITSpider(scrapy.Spider):
    name = "windtre_it"
    item_attributes = {
        "brand": "Wind Tre",
        "brand_wikidata": "Q28119223",
    }
    allowed_domains = ["windtre.it"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    start_urls = [
        "https://tools.windtre.it/trovanegozio/api.php?op=retriveShopWebService&data%5BcLat%5D=41.8928226&data%5BcLng%5D=12.4965158&data%5BrightUpCornerLat%5D=48.0&data%5BrightUpCornerLng%5D=19.0&data%5BleftDownCornerLat%5D=35.0&data%5BleftDownCornerLng%5D=6.0&data%5Bnegozio%5D=true&data%5Brivenditore%5D=false&data%5Bassistenza%5D=false&data%5Bdhl%5D=false&data%5Bteme%5D=windtre"
    ]

    def parse(self, response):
        data = response.json().get("data", [])
        for store in data:
            if store.get("tipologia") != "negozio":
                continue

            lat = store.get("lat")
            lon = store.get("lng")
            if not lat or not lon:
                continue

            item = Feature()
            item["ref"] = store.get("dealerid")
            item["lat"] = lat
            item["lon"] = lon

            if street_address := store.get("indirizzo"):
                item["street_address"] = street_address.strip()
            if city := store.get("comune"):
                item["city"] = city.strip()
            if state := store.get("siglaprov"):
                item["state"] = state.strip()
            if postcode := store.get("cap"):
                item["postcode"] = str(postcode).strip()
            item["country"] = "IT"

            if phone := store.get("telefono"):
                phone = phone.strip()
                if phone:
                    item["phone"] = phone

            if email := store.get("email"):
                email = email.strip()
                if email:
                    item["email"] = email

            item["website"] = "https://www.windtre.it/trova-negozio"

            apply_category(Categories.SHOP_TELECOMMUNICATION, item)
            yield item
