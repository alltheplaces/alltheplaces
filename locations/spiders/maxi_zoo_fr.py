from scrapy.http import Response

from locations.items import Feature
from locations.spiders.fressnapf_de import FressnapfDESpider


class MaxiZooFRSpider(FressnapfDESpider):
    name = "maxi_zoo_fr"
    item_attributes = {"brand": "Maxi Zoo", "brand_wikidata": "Q108403242"}
    api_key = "maxizooFR"
    website_format = "https://www.maxizoo.fr/stores/{}/"

    def post_process_item(self, item: Feature, response: Response, location: dict, **kwargs):
        item["branch"] = location["displayName"].removeprefix("Maxi Zoo ")

        yield item
