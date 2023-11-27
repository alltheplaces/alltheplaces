import re
from urllib.parse import unquote

from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class MidasAUSpider(Spider):
    name = "midas_au"
    item_attributes = {"brand": "Midas", "brand_wikidata": "Q118383658"}
    allowed_domains = ["www.midas.com.au"]
    start_urls = ["https://www.midas.com.au/wp-admin/admin-ajax.php?action=get_all_stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        results = Selector(text=response.json()["result_listing"])
        for location in results.xpath('//div[@class = "result-list"]'):
            properties = {
                "ref": location.xpath(".//h4/@data-index").get().strip(),
                "name": location.xpath(".//h4/text()").get().strip(),
                "lat": location.xpath(".//h4/@data-lat").get().strip(),
                "lon": location.xpath(".//h4/@data-lng").get().strip(),
                "addr_full": re.sub(r"\s{2,}", " ", " ".join(location.xpath(".//div/p[1]/text()").getall())).strip(),
                "website": location.xpath('.//div/p[1]/a[contains(@href, "/stores/")]/@href').get().strip(),
                "phone": location.xpath('.//div/p[2]/a[contains(@href, "tel:")]/@href')
                .get()
                .strip()
                .replace("tel:", ""),
                "email": unquote(
                    location.xpath('.//div/p[2]/a[contains(@href, "admin_email=")]/@href')
                    .get()
                    .strip()
                    .split("admin_email=", 1)[1]
                    .split('"', 1)[0]
                ),
            }
            hours_string = " ".join(location.xpath(".//table/tr/td/text()").getall())
            day_pairs = [
                ["Monday", "Tuesday"],
                ["Tuesday", "Wednesday"],
                ["Wednesday", "Thursday"],
                ["Thursday", "Friday"],
                ["Friday", "Saturday"],
                ["Saturday", "Sunday"],
                ["Sunday", "Monday"],
            ]
            for day_pair in day_pairs:
                if day_pair[0] not in hours_string and day_pair[1] not in hours_string:
                    hours_string = hours_string.replace("Today", day_pair[0]).replace("Tomorrow", day_pair[1])
                    break
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.SHOP_CAR_REPAIR, properties)
            yield Feature(**properties)
