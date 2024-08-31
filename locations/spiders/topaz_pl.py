from chompjs import parse_js_object
from scrapy import Request, Spider

from locations.categories import Categories
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class TopazPLSpider(Spider):
    name = "topaz_pl"
    item_attributes = {"brand": "Topaz", "brand_wikidata": "Q11837058", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["topaz24.pl"]
    start_urls = ["https://topaz24.pl/sklepy-topaz"]

    def extract_json(self, response):
        js_blob = (
            "["
            + response.xpath('//script[contains(text(), "var locations = [")]/text()')
            .get()
            .split("var locations = [", 1)[1]
            .split("];", 1)[0]
            + "]"
        )
        js_blob = js_blob.replace('\\"', "").replace("\\/", "/")
        return parse_js_object(js_blob, unicode_escape=True)

    def parse(self, response):
        for location in self.extract_json(response):
            properties = {
                "ref": location[0].split("<a href=/sklep/", 1)[1].split(">", 1)[0],
                "name": location[1],
                "lat": location[2],
                "lon": location[3],
                "street_address": location[0].split("<br />", 2)[0],
                "city": location[0].split("<br />", 2)[1],
                "website": "https://topaz24.pl" + location[0].split("<a href=", 1)[1].split(">", 1)[0],
            }
            yield Request(url=properties["website"], meta={"properties": properties}, callback=self.parse_store)

    def parse_store(self, response):
        properties = response.meta["properties"]
        properties["phone"] = list(
            filter(None, map(str.strip, response.xpath('//div[@id="shop"]/div[1]/div[4]/div[1]//text()').getall()))
        )[-1]
        hours_string = " ".join(
            filter(None, map(str.strip, response.xpath('//div[@id="shop"]/div[1]/div[4]/div[2]//text()').getall()))
        )
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_PL)
        yield Feature(**properties)
