import scrapy

from locations.items import Feature


class LibertyAUSpider(scrapy.Spider):
    name = "liberty_au"
    item_attributes = {"brand": "Liberty Oil", "brand_wikidata": "Q106687078"}
    allowed_domains = ["libertyconvenience.com.au"]
    start_urls = ["https://www.libertyconvenience.com.au/wp-admin/admin-ajax.php?action=store_search&autoload=1"]

    def parse_hours(store_hours):
        pass

    def parse(self, response):
        locations = response.json()
        for loc in locations:
            yield Feature(
                {
                    "ref": loc["id"],
                    "branch": loc["store"],
                    "street_address": loc["address"],
                    "city": loc["city"],
                    "state": loc["state"],
                    "postcode": loc["zip"],
                    "country": loc["country"],
                    "lat": loc["lat"],
                    "lon": loc["lng"],
                    "phone": loc["phone"],
                }
            )
