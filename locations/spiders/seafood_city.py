from scrapy.http import FormRequest
from locations.storefinders.store_locator_plus_self import StoreLocatorPlusSelfSpider


class SeafoodCitySpider(StoreLocatorPlusSelfSpider):
    name = "seafood_city"
    item_attributes = {
        "brand_wikidata": "Q7440359",
        "brand": "Seafood City",
    }
    max_results = 100

    def start_requests(self):
        url = f"https://www.seafoodcity.com/wp-admin/admin-ajax.php"
        lat = 37.09024
        lon = -95.712891
        formdata = {
            "action": "csl_ajax_onload",
            "lat": str(lat),
            "lng": str(lon),
            "radius": "",
            "nonce": "18e8e79bfe"
        }
        yield FormRequest(url=url, formdata=formdata, method="POST")
