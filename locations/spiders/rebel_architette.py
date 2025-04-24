import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class RebelArchitetteSpider(JSONBlobSpider):
    name = "rebel_architette"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://www.rebelarchitette.it/"]
    no_refs = True

    def extract_json(self, response):
        cdata = response.xpath('//script[contains(text(), "var eltdMultipleMapVars = ")]/text()').get()
        return chompjs.parse_js_object(cdata.split("var eltdMultipleMapVars = ")[1])["multiple"]["addresses"]

    def post_process_item(self, item, response, location):
        apply_category(Categories.OFFICE_ARCHITECT, item)
        if loc := location.get("location"):
            if addr := loc.get("address"):
                item["addr_full"] = addr
        item["name"] = item["name"].split(">")[-1].split("&gt;")[-1].strip()
        yield item
