import json
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

        if "Vente" in services:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, "Après-vente" in services)
        elif "Après-vente" in services:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        else:
            self.logger.error(f"Unknown type: {services}, {item['name']}, {item['ref']}")

        # TODO: hours

        yield item
