import chompjs
from scrapy import Selector
from scrapy.http import Response

from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class BerlinDonerKebapPLSpider(JSONBlobSpider):
    name = "berlin_doner_kebap_pl"
    item_attributes = {
        "brand": "Berlin Döner Kebap",
        "brand_wikidata": "Q126195313",
        "extras": {"amenity": "fast_food", "cuisine": "kebab"},
    }
    start_urls = ["https://www.berlindonerkebap.com/restauracje/wszystkie/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(),"gm_data")]/text()').get())

    def post_process_item(self, item, response: Response, location):
        sel = Selector(text=location["message"])
        item["addr_full"] = merge_address_lines(sel.xpath("//text()").getall()[1:])

        yield item
