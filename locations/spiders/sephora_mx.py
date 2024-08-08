import html
import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class SephoraMXSpider(Spider):
    name = "sephora_mx"
    item_attributes = {"brand": "Sephora", "brand_wikidata": "Q2408041"}
    allowed_domains = ["www.sephora.com.mx"]
    start_urls = ["https://www.sephora.com.mx/stores/"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        for location in response.xpath("//li[@data-storeaddress]"):
            properties = {
                "lat": location.xpath("./@data-latitude").get().strip(),
                "lon": location.xpath("./@data-longitude").get().strip(),
                "addr_full": re.sub(
                    r"\s*\d+$", "", html.unescape(location.xpath("./@data-storeaddress").get().strip())
                ),
                "postcode": re.search(r"(\d+)", location.xpath("./@data-zip").get()).group(1),
                "phone": location.xpath("./@data-phone").get().strip(),
            }
            properties["name"] = html.unescape(location.xpath("./@data-name").get().strip())
            if " - " in properties["name"]:
                properties["name"] = properties["name"].split(" - ", 1)[1]
            properties["ref"] = properties["name"].lower().replace(" ", "_")
            item = Feature(**properties)
            apply_category(Categories.SHOP_BEAUTY, item)
            yield item
