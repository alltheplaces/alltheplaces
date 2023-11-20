import json

from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MediaMarktSpider(StructuredDataSpider):
    name = "media_markt"
    item_attributes = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}
    start_urls = ["https://www.mediamarkt.de/de/store/store-finder"]
    user_agent = BROWSER_DEFAULT
    rules = [Rule(LinkExtractor(allow=r"https://www.mediamarkt.de/de/store/"), callback="parse_sd")]

    def _parse(self, response):
        script = response.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').extract_first()
        script = script[script.index("{") : script.rindex("}") + 1]
        state = json.loads(script)["apolloState"]["ROOT_QUERY"]['localStorePage({"uid":"store-finder"})']["content"]

        for item in state:
            if item.get("__typename") == "GraphqlLocalStorePageContentAccordion":
                for region in item["regions"]:
                    for store in region["regionStores"]:
                        yield Request(f"https://www.mediamarkt.de/de/store/{store['uid']}", callback=self.parse_sd)
