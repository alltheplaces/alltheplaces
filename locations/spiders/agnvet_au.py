import chompjs
from scrapy import Selector, Spider

from locations.dict_parser import DictParser


class AgnvetAUSpider(Spider):
    name = "agnvet_au"
    item_attributes = {
        "brand": "AGnVET",
        "brand_wikidata": "Q119263284",
        "extras": {
            "shop": "agrarian",
        },
    }
    allowed_domains = ["agnvet.com.au"]
    start_urls = ["https://agnvet.com.au/group/locations/"]

    def parse(self, response):
        data_raw = response.xpath("//script[contains(text(), '},\"places\":[{')]/text()").get()
        data_raw = data_raw.split('},"places":', 1)[1]
        locations = chompjs.parse_js_object(data_raw)
        for location in locations:
            item = DictParser.parse(location)
            item["city"] = location["location"]["city"]
            item["state"] = location["location"]["state"]
            item["postcode"] = location["location"]["postal_code"]
            phone_html = Selector(text=location["location"]["extra_fields"]["phone"])
            item["phone"] = phone_html.xpath('//a[contains(@href, "tel:")]/@href').get().replace("tel:", "")
            yield item
