from scrapy import Selector

from locations.categories import apply_category
from locations.json_blob_spider import JSONBlobSpider


class TyremartZASpider(JSONBlobSpider):
    name = "tyremart_za"
    item_attributes = {"brand": "Tyremart", "brand_wikidata": "Q123382009"}
    start_urls = ["https://www.tyremart.co.za/?action=remote&type=branch-list"]

    def post_process_item(self, item, response, branch):
        item["name"] = branch["post_title"]
        item["street_address"] = branch["meta"]["dealer-address"]
        item["lat"], item["lon"] = branch["meta"]["google-map-coords"].split(",")
        item["email"] = branch["meta"]["dealer-email"]
        item["phone"] = "; ".join(
            Selector(text=branch["meta"]["dealer-call"]).xpath('//a[contains(@href, "tel:")]/@href').getall()
        )
        item["website"] = branch["meta"]["dealer-promo-url"]
        apply_category({"shop": "tyres"}, item)
        yield item
