from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class UltraLiquorsZASpider(Spider):
    name = "ultra_liquors_za"
    item_attributes = {"brand": "Ultra Liquors", "brand_wikidata": "Q116620602"}
    allowed_domains = ["greenpoint.ultraliquors.co.za"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[FormRequest]:
        yield FormRequest(
            url="https://greenpoint.ultraliquors.co.za/UltraCityStoreSelector/ListData",
            formdata={"length": "1000"},
        )

    def parse(self, response, **kwargs):
        for data in response.json()["Data"]:
            data["address"] = data.pop("CompanyAddress")
            data["phone"] = data.pop("CompanyPhoneNumber")
            item = DictParser.parse(data)
            item["branch"] = item.pop("name")

            apply_yes_no(Extras.DELIVERY, item, data.get("IsDeliveryAvailable"))

            yield item
