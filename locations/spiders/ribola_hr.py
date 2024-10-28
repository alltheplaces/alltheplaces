from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class RibolaHRSpider(JSONBlobSpider):
    name = "ribola_hr"
    item_attributes = {
        "brand": "Ribola",
        "brand_wikidata": "Q65124070",
    }
    start_urls = [
        "https://ribola.hr/wp-json/wpgmza/v1/features/base64eJyrVkrLzClJLVKyUqqOUcpNLIjPTIlRsopRMjSIUdIBiRRnlBZ4uhQDBaNjgQLJpcUl+blumak5KRCxWqVaABXJFuo"
    ]
    locations_key = "markers"

    def post_process_item(self, item, response, location):
        item["name"] = None
        apply_category(Categories.SHOP_SUPERMARKET, item)
        # TODO: hours
        yield item
