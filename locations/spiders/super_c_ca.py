from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.linked_data_parser import LinkedDataParser


class SuperCCASpider(SitemapSpider):
    name = "super_c_ca"
    item_attributes = {"brand": "Super C", "brand_wikidata": "Q3504127", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.superc.ca"]
    sitemap_urls = ["https://www.superc.ca/sitemap-general-en.xml"]
    sitemap_rules = [(r"^https:\/\/www\.superc\.ca\/en\/find-a-grocery\/\d+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # HTTP 500 for robots.txt
    download_delay = (
        65  # HTTP 429 rate limiting applies with retry_after=65 (only need ~5 requests in a row to trigger)
    )

    def parse(self, response):
        js_blob = (
            response.xpath('//script[contains(text(), "var storeJsonLd = ")]/text()')
            .get()
            .replace("\\n", "")
            .replace('\\"', '"')
        )
        json_ld_data = parse_js_object(js_blob.split('var storeJsonLd = "', 1)[1].split('";', 1)[0])
        item = LinkedDataParser.parse_ld(json_ld_data)
        item["ref"] = json_ld_data["id"].split("/find-a-grocery/", 1)[1]
        item["branch"] = item["name"].removeprefix("Super C - ")
        yield item
