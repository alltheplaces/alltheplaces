from chompjs import parse_js_object
from scrapy import Selector, Spider

from locations.categories import Categories
from locations.hours import OpeningHours
from locations.items import Feature


class TheGoodFeetStoreSpider(Spider):
    name = "the_good_feet_store"
    item_attributes = {
        "brand": "The Good Feet Store",
        "brand_wikidata": "Q122031157",
        "extras": Categories.SHOP_SHOES.value,
    }
    allowed_domains = ["www.goodfeet.com"]
    start_urls = ["https://www.goodfeet.com/locations"]

    def extract_json(self, response):
        js_blob = response.xpath('//script[contains(text(), "var addresses = [[")]/text()').get()
        js_blob = "[[" + js_blob.split("var addresses = [[", 1)[1].split("]];", 1)[0] + "]]"
        return parse_js_object(js_blob)

    def parse(self, response):
        for location in self.extract_json(response):
            location_html = Selector(text=location[1])
            all_text = " ".join(location_html.xpath("//text()").getall())
            if "COMING SOON" in all_text.upper():
                continue
            properties = {
                "ref": location_html.xpath("//h4/a/@href").get(),
                "name": location_html.xpath("//h4/a/text()").get(),
                "lat": location[-2],
                "lon": location[-1],
                "addr_full": location[0],
                "phone": location_html.xpath('//a[contains(@href, "tel:")]/@href').get(),
                "website": location_html.xpath("//h4/a/@href").get(),
            }
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(all_text)
            yield Feature(**properties)
