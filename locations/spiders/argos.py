import re

from scrapy.spiders import SitemapSpider

from locations.spiders.sainsburys import SainsburysSpider
from locations.spiders.tesco_gb import set_located_in
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class ArgosSpider(SitemapSpider, StructuredDataSpider):
    name = "argos"
    item_attributes = {"brand": "Argos", "brand_wikidata": "Q4789707"}
    sitemap_urls = ["https://www.argos.co.uk/stores_sitemap.xml"]
    sitemap_rules = [(r"https://www.argos.co.uk/stores/([\d]+)-([\w-]+)", "parse")]
    user_agent = BROWSER_DEFAULT
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("Closed - "):
            return

        if m := re.search(r"((?:in|inside|) Sainsbury'?s?)", item["name"], flags=re.IGNORECASE):
            item["name"] = item["name"].replace(m.group(1), "").strip()
            set_located_in(SainsburysSpider.SAINSBURYS, item)
        if item["name"].endswith(" Local"):
            item["name"] = item["name"].removesuffix(" Local")
            set_located_in(SainsburysSpider.SAINSBURYS_LOCAL, item)

        if m := re.search(r'"type":(\d),"lat":(-?\d+\.\d+),"lng":(-?\d+\.\d+),', response.text):
            store_type, item["lat"], item["lon"] = m.groups()
            if store_type == "1" or "Collection Point" in item["name"] or "CP" in item["name"]:
                return

        yield item
