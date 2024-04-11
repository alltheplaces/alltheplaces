from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.central_england_cooperative import set_operator


class EwivaITSpider(Spider):
    name = "ewiva_it"
    EWIVA = {"brand": "Ewiva", "brand_wikidata": "Q123272416"}
    start_urls = ["https://ewiva.com/wp-content/themes/ewiva/sedi.json"]

    def parse(self, response, **kwargs):
        for location in response.json():
            if location["status"] != "In Operation":
                continue
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["siteName"]
            item["addr_full"] = location["streetAddress"]
            item["lat"] = location["lat"]
            item["lon"] = location.get("lng")
            item["state"] = location["region"]
            item["city"] = location["city"]
            # TODO: cu100kw cu150kw cu350kw pocTot

            apply_category(Categories.CHARGING_STATION, item)
            set_operator(self.EWIVA, item)

            yield item
