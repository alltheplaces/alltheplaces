from typing import Any

from scrapy.http import Response

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class EightyFiveDegreesCAUSpider(CamoufoxSpider):
    name = "eighty_five_degrees_c_au"
    item_attributes = {"brand": "85°C Bakery Cafe", "brand_wikidata": "Q4644852"}
    start_urls = ["https://www.85cafe.com.au/store-finder/"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath("//div[@class='card mb-2']"):
            item = Feature()
            item["website"] = store.xpath(".//h2/a/@href").get()
            item["ref"] = item["website"].split("/")[-1]
            item["branch"] = store.xpath(".//h2/a/text()").get().removeprefix("85C Daily Cafe ")
            item["addr_full"] = store.xpath("string(.//address/p[1])").get()
            item["phone"] = store.xpath("string(.//address/p[2])").get()

            extract_google_position(item, store)
            apply_category(Categories.CAFE, item)

            yield item
