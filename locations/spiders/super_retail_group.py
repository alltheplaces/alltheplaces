import json
import re
from html import unescape

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class SuperRetailGroupSpider(SitemapSpider, StructuredDataSpider):
    name = "super_retail_group"
    brands = {
        "bcf": ["BCF", "Q16246527"],
        "rebel": ["Rebel", "Q18636397"],
        "sca": ["Supercheap Auto", "Q7643119"],
    }
    sitemap_urls = [
        "https://www.bcf.com.au/sitemap-stores.xml",
        # No BCF stores in New Zealand
        "https://www.rebelsport.com.au/sitemap-stores.xml",
        # Rebel New Zealand uses a different store finder method
        "https://www.supercheapauto.com.au/sitemap-stores.xml",
        "https://www.supercheapauto.co.nz/sitemap-stores.xml",
    ]
    sitemap_rules = [(r"\/stores\/details\/(?:bcf|rebel|sca)-[\w\-]+$", "parse_sd")]
    time_format = "%I:%M %p"

    def post_process_item(self, item, response, ld_data):
        sid_list = "|".join(self.brands.keys())
        m = re.search(r"\/stores\/details\/(" + sid_list + r")-", response.url)
        if not m:
            return
        sid = m.group(1)
        if sid not in self.brands.keys():
            return
        item["brand"] = self.brands[sid][0]
        item["brand_wikidata"] = self.brands[sid][1]

        data_raw = unescape(response.xpath('//div[@id="store-locator-details-map"]/@data-store-object').get())
        location = json.loads(data_raw)
        item["ref"] = location["storeID"]
        item["name"] = location["name"]
        item["lat"] = location["lat"]
        item["lon"] = location["lng"]

        item.pop("image", None)
        item.pop("facebook", None)

        yield item
