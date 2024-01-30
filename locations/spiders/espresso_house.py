from chompjs import parse_js_object
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class EspressoHouseSpider(SitemapSpider):
    name = "espresso_house"
    item_attributes = {"brand": "Espresso House", "brand_wikidata": "Q10489162"}
    allowed_domains = ["espressohouse.com"]

    sitemap_urls = ["https://espressohouse.com/sitemap.xml"]
    sitemap_rules = [("/en/find-us/.+", "parse_location")]

    def parse_location(self, response: Response):
        next_data = response.css("#__NEXT_DATA__::text").get()
        shop_details = parse_js_object(next_data)["props"]["pageProps"]["data"]["coffeeShop"]
        item = DictParser.parse(shop_details)
        item["ref"] = shop_details["coffeeShopId"]
        street_address = shop_details["address1"] if shop_details["address1"] else shop_details["address2"]
        item["street_address"] = street_address.split(",")[0].strip()
        item["branch"] = shop_details["coffeeShopName"]
        item["website"] = response.url
        try:
            opening_hours = OpeningHours()
            for day in shop_details["openingHours"]:
                opening_hours.add_range(
                    day["weekDay"].replace("Mittwoch", "Wednesday"),
                    day["openFrom"].removesuffix(":00"),
                    day["openTo"].removesuffix(":00"),
                )
            item["opening_hours"] = opening_hours
        except:
            pass
        yield item
