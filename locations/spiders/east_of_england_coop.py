from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class EastOfEnglandCoopSpider(SitemapSpider):
    name = "east_of_england_coop"
    item_attributes = {
        "brand": "East of England Co-op",
        "brand_wikidata": "Q5329759",
        "country": "GB",
    }
    sitemap_urls = ["https://www.eastofengland.coop/googlesitemap.xml"]
    sitemap_rules = [
        (
            r"https:\/\/www\.eastofengland\.coop\/(supermarket|foodstores|funerals)\/",
            "parse_item",
        )
    ]

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].replace("food/stores", "foodstores")
            yield entry

    def parse_item(self, response):
        MicrodataParser.convert_to_json_ld(response)
        item = LinkedDataParser.parse(response, "Store")

        if item is None:
            return

        if isinstance(item.get("street_address"), list):
            item["street_address"].reverse()
            item["street_address"] = ", ".join(item["street_address"])

        item["ref"] = item["website"]

        if item.get("lat") is None:
            item["lat"] = response.xpath('//div[@class="store-map"]/@data-lat').get()
        if item.get("lon") is None:
            item["lon"] = response.xpath('//div[@class="store-map"]/@data-long').get()

        apply_category(Categories.SHOP_SUPERMARKET, item)
        return item
