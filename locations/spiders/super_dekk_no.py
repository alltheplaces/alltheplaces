import re

import chompjs
from scrapy import Selector, Spider

from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class SuperDekkNOSpider(Spider):
    name = "super_dekk_no"
    item_attributes = {"brand": "Super Dekk", "brand_wikidata": "Q120765135"}
    start_urls = ["https://www.superdekk.no/map.php"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        locations = chompjs.parse_js_object(re.search(r"var positions = (\[.+\]);", response.text, re.DOTALL).group(1))
        for name, lat, lon, popup_html in locations:
            item = Feature()
            item["name"] = name
            item["lat"] = lat
            item["lon"] = lon

            sel = Selector(text=popup_html)

            item["ref"] = item["website"] = response.urljoin(sel.xpath("//a/@href").get())
            item["addr_full"] = clean_address(sel.xpath("/html/body/text()").getall())

            yield item
