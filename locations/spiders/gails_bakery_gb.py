from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class GailsBakeryGBSpider(SitemapSpider):
    name = "gails_bakery_gb"
    item_attributes = {"brand": "GAIL's Bakery", "brand_wikidata": "Q110662562", "extras": Categories.SHOP_BAKERY.value}
    allowed_domains = ["gailsbread.co.uk"]
    sitemap_urls = ["https://gailsbread.co.uk/wpsl_stores-sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/gailsbread\.co\.uk\/bakeries\/[^\/]+\/?$", "parse")]

    def parse(self, response):
        js_blob = response.xpath('//script[@id="wpsl-js-js-extra"]/text()').get()
        js_blob = "{" + js_blob.split("var wpslMap_0 = {", 1)[1].split("};", 1)[0] + "}"
        location = parse_js_object(js_blob)["locations"][0]
        item = DictParser.parse(location)
        item["name"] = " ".join(
            filter(None, map(str.strip, response.xpath('//h1[@class="slideshow-title"]/text()').getall()))
        )
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = response.url

        hours_string = " ".join(
            filter(None, map(str.strip, response.xpath('//ul[@class="opening-hours"]//text()').getall()))
        )
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(hours_string)

        yield item
