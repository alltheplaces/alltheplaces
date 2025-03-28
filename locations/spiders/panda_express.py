from scrapy import FormRequest
from scrapy.http import JsonRequest

from locations.storefinders.nomnom import NomNomSpider, slugify
from locations.user_agents import BROWSER_DEFAULT


class PandaExpressSpider(NomNomSpider):
    name = "panda_express"
    item_attributes = {"brand": "Panda Express", "brand_wikidata": "Q1358690"}
    domain = "pandaexpress.com"
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}
    use_calendar = False

    def start_requests(self):
        # Fetch cookies to avoid DataDome captcha blockage
        yield FormRequest(
            url="https://api-js.datadome.co/js/",
            headers={
                "referer": "https://www.pandaexpress.com/",
            },
            formdata={"ddk": "988C29D6706800A8C3451C0AB0E93A"},
        )

    def parse(self, response):
        yield JsonRequest(
            url="https://nomnom-prod-api.pandaexpress.com/restaurants",
            cookies={"cookie": response.json()["cookie"]},
            callback=self.parse_locations,
        )

    def post_process_item(self, item, response, feature):
        item["website"] = (
            f"https://www.pandaexpress.com/locations/{slugify(feature['state'])}/{slugify(feature['city'])}/{feature['extref']}"
        )
        yield item
