import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class DrummondGolfAUSpider(SitemapSpider, StructuredDataSpider):
    name = "drummond_golf_au"
    item_attributes = {"brand": "Drummond Golf", "brand_wikidata": "Q124065894"}
    # start_urls = ["https://www.drummondgolf.com.au/amlocator/index/ajax/?p=1"]
    sitemap_urls = ["https://drummondgolf.com.au/sitemap.xml"]
    sitemap_rules = [("/pages/stores/", "parse_sd")]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    wanted_types = ["Organization"]
    #
    # def pre_process_data(self, ld_data: dict, **kwargs) -> None:
    #     if not ld_data.get("postalCode"):
    #         return None

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # print(ld_data)
        if item.get("street_address"):
            item["lat"], item["lon"] = re.search(
                r"\"coordinates\":\s*\"(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)\"", response.xpath("//@data-markers").get()
            ).groups()
            item["branch"] = response.xpath("//title/text()").get().removesuffix(" Drummond Golf")
            yield item

    # def parse(self, response, **kwargs):
    #     if raw_data := re.search(r"items\":(\[.*\]),\"", response.text):
    #         for store in json.loads(raw_data.group(1)):
    #             item = DictParser.parse(store)
    #             popup_html = Selector(text=store["popup_html"])
    #             item["website"] = popup_html.xpath('//*[@class= "amlocator-link"]/@href').get().replace(" ", "")
    #             address_string = re.sub(r"\s+", " ", " ".join(filter(None, popup_html.xpath("//text()").getall())))
    #             item["city"] = address_string.split("City: ", 1)[1].split(" Zip: ", 1)[0]
    #             item["postcode"] = address_string.split("Zip: ", 1)[1].split(" Address: ", 1)[0]
    #             item["street_address"] = address_string.split("Address: ", 1)[1].split(" State: ", 1)[0]
    #             item["state"] = address_string.split("State: ", 1)[1].split(" Description: ", 1)[0]
    #             apply_category(Categories.SHOP_SPORTS, item)
    #             item["extras"]["sports"] = "golf"
    #             yield item
    #         if next_url := re.search(r"action next.*href=\\\"(.*)\"\s*rel", response.text):
    #             yield scrapy.Request(url=next_url.group(1).replace("\\", ""), callback=self.parse)
