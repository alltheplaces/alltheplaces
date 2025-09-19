import json
from copy import deepcopy
from urllib.parse import urlparse

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class MitsubishiFRSpider(XMLFeedSpider):
    name = "mitsubishi_fr"
    start_urls = [
        "https://www.mitsubishi-motors.fr/locator/concessions?lat=48.856614&lng=2.3522219000000177&radius=10000000&services_string=1,2&locate=0"
    ]
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    iterator = "xml"
    itertag = "marker"

    def build_sales_item(self, item):
        sales_item = deepcopy(item)
        sales_item["ref"] = f"{item['ref']}-sales"
        apply_category(Categories.SHOP_CAR, sales_item)
        return sales_item

    def build_service_item(self, item):
        service_item = deepcopy(item)
        service_item["ref"] = f"{item['ref']}-service"
        apply_category(Categories.SHOP_CAR_REPAIR, service_item)
        return service_item

    def parse_node(self, response: Response, node: Selector):
        item = Feature()
        item["ref"] = node.xpath("./@concessionnaire_id").get()
        item["name"] = node.xpath("./@garage").get()  # this name is shown in the website
        item["extras"]["alt_name"] = node.xpath("./@name").get()  # this is name of a dealer
        item["addr_full"] = node.xpath("./@address").get()
        item["city"] = node.xpath("./@ville").get()
        item["postcode"] = node.xpath("./@cp").get()
        item["phone"] = node.xpath("./@phone").get()
        item["lat"] = node.xpath("./@lat").get()
        item["lon"] = node.xpath("./@lng").get()
        item["website"] = (
            node.xpath("./@concessionnaire_url").get(default=None) or "https://" + urlparse(response.url).netloc
        )

        if item["website"] and not item["website"].startswith("http"):
            item["website"] = "https://" + item["website"]

        services = json.loads(node.xpath("./@services").get())
        services = [service["name"] for service in services]

        sales_available = "Vente" in services
        service_available = "Après-vente" in services

        if sales_available:
            sales_item = self.build_sales_item(item)
            apply_yes_no(Extras.CAR_REPAIR, sales_item, service_available)
            yield sales_item

        if service_available:
            service_item = self.build_service_item(item)
            yield service_item

        if not sales_available and not service_available:
            self.logger.error(f"Unknown type: {services}, {item['name']}, {item['ref']}")

        # TODO: hours
