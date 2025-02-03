from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HTPawnbrokersGBSpider(JSONBlobSpider):
    name = "h_t_pawnbrokers"
    item_attributes = {"brand": "H&T Pawnbrokers", "brand_wikidata": "Q105672451"}
    start_urls = ["https://as-handt-store-address-service.azurewebsites.net/api/AllStoreData"]




