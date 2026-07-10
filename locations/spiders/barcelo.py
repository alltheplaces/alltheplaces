import chompjs
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class BarceloSpider(StructuredDataSpider):
    name = "barcelo"
    item_attributes = {"brand_wikidata": "Q15148996"}
    brand_map = {
        "allegro": "Allegro Hotels",
        "barcelo": "Barceló Hotels & Resorts",
        "occidental": "Occidental",
        "royal hideaway": "Royal Hideaway",
    }
    start_urls = ["https://www.barcelo.com/en-us/hotels/"]
    link_extractor = LinkExtractor(tags=["div"], attrs=["data-card-id"])
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    search_for_twitter = False
    search_for_facebook = False

    def parse(self, response: Response, **kwargs):
        for link in self.link_extractor.extract_links(response):
            url = link.url.replace("/content/barcelo/us/en-us/", "/en-us/")
            if not url.endswith("/"):
                url = url + "/"
            yield Request(url=url, callback=self.parse_sd)

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"], item["lon"] = url_to_coords(ld_data.get("hasMap", ""))
        item["city"] = item.pop("state")
        item["opening_hours"] = None
        if brand_script := response.xpath('//script[contains(text(),"hotel_brand")]/text()').get():
            brand = chompjs.parse_js_object(brand_script).get("hotel_brand")
            if brand != "part of barcelo hotel group":
                item["brand"] = self.brand_map.get(brand)
        if "Resort" in item["name"]:
            apply_category(Categories.LEISURE_RESORT, item)
        else:
            apply_category(Categories.HOTEL, item)
        yield item
