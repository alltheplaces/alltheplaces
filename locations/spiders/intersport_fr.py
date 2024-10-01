import re

import chompjs
import scrapy
from scrapy import Request, Selector

from locations.categories import Categories
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class IntersportFRSpider(scrapy.Spider):
    name = "intersport_fr"
    item_attributes = {"brand": "Intersport", "brand_wikidata": "Q666888", "extras": Categories.SHOP_SPORTS.value}
    start_url = "https://www.intersport.fr/store-finder/"

    def start_requests(self):
        # Need to make the request more browser-like to be accepted
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.8,fr-FR;q=0.5,fr;q=0.3",
            "User-Agent": BROWSER_DEFAULT,
        }
        yield Request(url=self.start_url, headers=headers, callback=self.parse)

    def parse(self, response, **kwargs):
        store_data = response.xpath('//div[@id="map_canvas"]/@data-stores').get()
        store_data_cleaned = store_data.replace("\n", "").replace("\t", " ")
        stores = chompjs.parse_js_object(store_data_cleaned)
        ref_regexp = re.compile(r"<a href='/store/(\d+_\d+)-")
        for _, store in stores.items():
            content_text = Selector(text=store["content"]).xpath("//text()").getall()
            ref = ref_regexp.search(store["content"]).group(1)
            if 1000 <= int(ref) < 2000:
                country = "BE"
            else:
                country = "FR"
            yield Feature(
                {
                    "ref": ref,
                    "name": store["name"].title(),
                    "lon": store["longitude"],
                    "lat": store["latitude"],
                    "addr_full": content_text[2],
                    "phone": content_text[1].rsplit(maxsplit=1)[1],
                    "country": country,
                }
            )
