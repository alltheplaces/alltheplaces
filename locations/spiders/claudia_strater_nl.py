import chompjs

from locations.json_blob_spider import JSONBlobSpider


class ClaudiaStraterNLSpider(JSONBlobSpider):
    name = "claudia_strater_nl"
    item_attributes = {
        "brand_wikidata": "Q52903369",
        "brand": "Claudia Sträter",
    }
    start_urls = ["https://www.claudiastrater.com/over-ons/winkels/"]
    no_refs = True

    def extract_json(self, response):
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "map.markers = ")]/text()').get().split("map.markers = ")[1]
        )

    def post_process_item(self, item, response, location):
        item["name"] = item["name"].strip()
        item["website"] = location["url"].replace("~/", "https://www.claudiastrater.com/")
        item["image"] = location["imageurl"].replace("~/", "https://www.claudiastrater.com/")

        yield item
