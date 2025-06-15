from chompjs import parse_js_object
from typing import Iterable

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FamilymartMYSpider(Spider):
    name = "familymart_my"
    item_attributes = {"brand": "FamilyMart", "brand_wikidata": "Q11247682"}
    allowed_domains = ["familymart.com.my"]
    start_urls = ["https://familymart.com.my/our-stores.html"]

    def parse(self, response: Response) -> Iterable[Feature]:
        js_blob = response.xpath('//script[contains(text(), "var data = [ // map data")]/text()').get()
        js_blob = "[" + js_blob.split("var data = [ // map data", 1)[1].split("]//]]>", 1)[0] + "]"
        js_blob = js_blob.replace("id': 86-1,", "id': 86,")
        features = parse_js_object(js_blob)
        for feature in features:
            description_html = Selector(text=feature["content"])
            properties = {
                "ref": str(feature["id"]),
                "lat": feature["position"]["lat"],
                "lon": feature["position"]["lng"],
                "branch": description_html.xpath('//h5/span/text()').get(),
                "addr_full": merge_address_lines(description_html.xpath('//p/text()').getall()),
            }
            apply_category(Categories.SHOP_CONVENIENCE, properties)
            yield Feature(**properties)
