from typing import Any
import json

from scrapy.http import HtmlResponse
from scrapy.spiders import Spider
from locations.pipelines.address_clean_up import merge_address_lines
from urllib.parse import urljoin
from scrapy.http import Response
from locations.items import Feature

class SweatyBettySpider(Spider):
    name = "Sweaty Betty"
    item_attributes = {"brand": "Sweaty Betty", "brand_wikidata": "Q7654224"}
    start_urls = ["https://www.sweatybetty.com/shop-finder"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        content = response.xpath('//script[@id="mobify-data"]/text()').get()
        data = json.loads(content)
        for area in data["__PRELOADED_STATE__"]["pageProps"]["allShops"]:
          for location in area["stores"]:

            item = Feature()
            item["ref"] = location["storeId"]
            item["branch"] = location["name"]
#            item["lat"] = location["addressLocation"]["lat"]
#            item["lon"] = location["addressLocation"]["lon"]
            item["branch"] = location["title"]
            item["street_address"] = merge_address_lines([location["address1"], location["address2"], location["city"]])
            item["city"] = location["city"]
            item["postcode"] = location["postalCode"]
            item["phone"] = location["phone"]

#            if location.get("storeHours"):
#               item["opening_hours"] = OpeningHours()
#               for day in map(str.lower, DAYS_FULL):
#                  item["opening_hours"].add_range(
#                      day,
#                      location["storeHours"]["{}Open".format(day)].strip(),
#                      location["storeHours"]["{}Close".format(day)].strip(),
#                  )

            s=location["name"]
            slug="".join(s.split()).lower() + "-" + location["storeId"]
            item["website"] = urljoin("https://www.sweatybetty.com/shop-details/", slug)

            yield item
