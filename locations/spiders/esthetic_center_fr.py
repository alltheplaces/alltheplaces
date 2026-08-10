import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature


class EstheticCenterFRSpider(SitemapSpider):
    name = "esthetic_center_fr"
    item_attributes = {"brand": "Esthetic Center", "brand_wikidata": "Q123321775"}
    sitemap_urls = ["https://www.esthetic-center.com/institut-sitemap.xml"]
    sitemap_rules = [("/trouver-institut/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = response.url.strip("/").split("/")[-1]
        item["website"] = response.url
        item["branch"] = response.xpath("//h1/span/text()").get("").removeprefix("Esthetic Center ")
        item["addr_full"] = response.xpath("//div[contains(@id, 'text_block-238')]/span/text()").get()
        item["phone"] = (
            response.xpath("//a[contains(@href, 'tel:')]/@href").get("").replace("tel:", "").replace(" ", "")
        )

        script_content = response.text
        item["lat"] = re.search(r'var latitude = "(.*?)";', script_content).group(1)
        item["lon"] = re.search(r'var longitude = "(.*?)";', script_content).group(1)

        oh = OpeningHours()
        for row in response.xpath("//div[contains(@class, 'horaire-row')]"):
            day = row.xpath(".//span[contains(@class, 'horaire-jour')]/text()").get()
            time_str = row.xpath(".//span[contains(@class, 'horaire-heures')]/text()").get()

            if day and time_str:
                oh.add_ranges_from_string(
                    f"{day} {time_str.replace('h', ':')}", days=DAYS_FR, closed=CLOSED_FR, delimiters=DELIMITERS_FR
                )

        item["opening_hours"] = oh
        apply_category(Categories.SHOP_BEAUTY, item)

        yield item
