import json
import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.structured_data_spider import StructuredDataSpider


class TargetUSSpider(SitemapSpider, StructuredDataSpider):
    name = "target_us"
    item_attributes = {"brand": "Target", "brand_wikidata": "Q1046951"}
    allowed_domains = ["target.com"]
    sitemap_urls = ["https://www.target.com/sitemap_stores-index.xml.gz"]
    wanted_types = ["DepartmentStore"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        script = response.xpath('//script[contains(text(), "__TGT_DATA__")]/text()').get()
        data = json.loads(json.loads(re.search(r"'__TGT_DATA__':.+JSON\.parse\((\"{.+}\")\)", script).group(1)))
        store_format = DictParser.get_nested_key(data, "physical_specifications").get("format")

        if store_format == "SuperTarget":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif store_format == "Pfresh":
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        elif store_format == "Gen Merch":
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        elif store_format == "TargetExpress":
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
        else:
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)
            self.crawler.stats.inc_value(f"atp/target_us/unmapped_category/{store_format}")

        item["extras"]["store_format"] = store_format

        yield item
