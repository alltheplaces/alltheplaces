from chompjs import parse_js_object
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


# AU, CA, GB, GU, IE, NL, NZ, PR, US, VI
class SunglassHut1Spider(SitemapSpider, StructuredDataSpider):
    name = "sunglass_hut_1"
    item_attributes = {"brand": "Sunglass Hut", "brand_wikidata": "Q136311"}
    allowed_domains = ["stores.sunglasshut.com"]
    sitemap_urls = ["https://stores.sunglasshut.com/robots.txt"]

    def post_process_item(self, item, response, ld_data):
        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        if "image" in item:
            item.pop("image")
        location = parse_js_object(response.xpath('.//script[contains(text(), "__INITIAL__DATA__")]/text()').get())
        item["extras"]["ref:google"] = data["document"].get("googlePlaceId")
        item["lat"] = data["document"]["yextDisplayCoordinate"]["latitude"]
        item["lon"] = data["document"]["yextDisplayCoordinate"]["longitude"]
        yield item
