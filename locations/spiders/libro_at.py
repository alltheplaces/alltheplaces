import json

from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class LibroATSpider(AmastyStoreLocatorSpider):
    name = "libro_at"
    item_attributes = {"brand": "Libro", "brand_wikidata": "Q1823138"}
    start_urls = ["https://www.libro.at/rest/V1/mthecom/storelocator/locations"]

    def parse(self, response, **kwargs):
        yield from self.parse_items(json.loads(response.xpath("/response/text()").get())["items"])

    def parse_item(self, item, location, popup_html):
        item["ref"], item["street_address"] = item.pop("name").split(": ", 1)

        yield item
