import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class MisensoCHSpider(scrapy.Spider):
    name = "misenso_ch"
    allowed_domains = ["misenso.ch"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        url = "https://www.misenso.ch/store/locator/vals"
        query = {"jsonrpc": "2.0", "method": "call", "params": {}, "id": 123}
        return [scrapy.http.JsonRequest(url, data=query)]

    def parse(self, response):
        for store in response.json()["result"]["map_stores_data"].values():
            address = store["store_address"]
            feature = Feature(
                brand="Misenso",
                brand_wikidata="Q116151325",
                city=address[1],
                country="CH",
                email=address[9],
                branch=store["store_name"],
                extras={"healthcare": "audiologist;optometrist"},
                lat=float(store["store_lat"]),
                lon=float(store["store_lng"]),
                name="Misenso",
                image=self.parse_image(response, store),
                phone=address[6],
                postcode=address[4],
                ref=str(store["store_id"]),
                street_address=address[0],
            )
            apply_category(Categories.SHOP_OPTICIAN, feature)
            yield feature

    @staticmethod
    def parse_image(response, store):
        if image := store["store_image"]:
            return response.urljoin(image).split("?")[0]  # strip off tracking id
        else:
            return None
