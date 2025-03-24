import chompjs
from scrapy.http import Response

from locations.json_blob_spider import JSONBlobSpider


class MitsubishiUASpider(JSONBlobSpider):
    name = "mitsubishi_ua"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://mitsubishi-motors.com.ua/find-a-dealer"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.__NUXT__")]/text()').re_first(
                r"dealers\s*=\s*\'(\[.+?\])\'"
            ),
            unicode_escape=True,
        )
