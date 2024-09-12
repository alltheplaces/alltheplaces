import chompjs

from locations.json_blob_spider import JSONBlobSpider


class PrimaprixSpider(JSONBlobSpider):
    name = "primaprix"
    item_attributes = {"brand": "Primaprix", "brand_wikidata": "Q112691161"}
    allowed_domains = ["primaprix.eu"]
    start_urls = ("https://primaprix.eu/es/localiza-tu-tienda/",)

    def extract_json(self, response):
        data = response.xpath('//script[contains(text(), "window.shops = ")]/text()').get().split("window.shops = ")[1]
        return chompjs.parse_js_object(data)
