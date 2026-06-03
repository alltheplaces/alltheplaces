from locations.playwright_spider import PlaywrightSpider
from locations.spiders.forever_new_au_nz import FOREVER_NEW_SHARED_ATTRIBUTES, ForeverNewAUNZSpider


class EverNewCASpider(ForeverNewAUNZSpider, PlaywrightSpider):
    name = "ever_new_ca"
    item_attributes = FOREVER_NEW_SHARED_ATTRIBUTES
    item_attributes["brand"] = "Ever New"
    start_urls = [
        "https://www.evernew.ca/locator/index/search/?address=vancouver&components[country]=CA&radius=10000000&type=all",
    ]
    # custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    #
    # def extract_json(self, response: TextResponse):
    #     data = json.loads(response.xpath("//pre/text()").get())["results"]["results"]
    #     return data
