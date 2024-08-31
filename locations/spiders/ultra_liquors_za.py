import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class UltraLiquorsZASpider(scrapy.Spider):
    name = "ultra_liquors_za"
    item_attributes = {"brand": "Ultra Liquors", "brand_wikidata": "Q116620602"}
    allowed_domains = ["greenpoint.ultraliquors.co.za"]
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        yield scrapy.FormRequest(
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
