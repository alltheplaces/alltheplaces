import json

from locations.json_blob_spider import JSONBlobSpider
from locations.user_agents import BROWSER_DEFAULT


class MindGBSpider(JSONBlobSpider):
    name = "mind_gb"
    item_attributes = {"brand": "Mind", "brand_wikidata": "Q3314763"}
    start_urls = ["https://www.mind.org.uk/mind-charity-shops/find-our-local-mind-shops/"]
    requires_proxy = True 
    #custom_settings = {
    #    "USER_AGENT": BROWSER_DEFAULT,
    #    "ROBOTSTXT_OBEY": False,
    #}

    def extract_json(self, response):
        script = response.xpath("//script[contains(text(), 'const locations')]/text()").get()
        starter = "const locations = "
        begin = script.find(starter) + len(starter)
        end = script.find('";', begin + 1) + 1
        return json.loads(json.loads(script[begin:end]))

    def post_process_item(self, item, response, feature):
        yield item
