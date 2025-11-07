from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class EmpresUSSpider(Spider):
    name = "empres_us"
    item_attributes = {"brand": "EmpRes", "brand_wikidata": "Q123370276"}
    allowed_domains = ["www.empres.com"]
    start_urls = ["https://www.empres.com/wp-admin/admin-ajax.php"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[FormRequest]:
        formdata = {
            "within": "200",
            "state": "",
            "service": "",
            "action": "block_locations_get",
            "position": "",
        }
        headers = {
            "Origin": "https://www.empres.com",
            "Referer": "https://www.empres.com/locations/",
            "X-Requested-With": "XMLHttpRequest",
        }
        for url in self.start_urls:
            yield FormRequest(url=url, formdata=formdata, headers=headers, method="POST")

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["website"] = location.get("link")
            item["street_address"] = item.pop("street", None)

            apply_category(Categories.CLINIC, item)

            yield item
