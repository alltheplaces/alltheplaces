from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class HalfordsGBSpider(CrawlSpider, StructuredDataSpider):
    name = "halfords_gb"
    start_urls = ["https://www.halfords.com/locations"]
    rules = [Rule(LinkExtractor(r"/locations/([^/]+)/$"), "parse")]
    wanted_types = ["AutomotiveBusiness", "LocalBusiness"]
    search_for_facebook = False
    search_for_twitter = False

    def pre_process_data(self, ld_data, **kwargs):
        for rule in ld_data.get("openingHoursSpecification") or []:
            rule["opens"] = (rule.get("opens") or "").strip()
            rule["closes"] = (rule.get("closes") or "").strip()

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = item.pop("name")
        if name.startswith("Halfords Autocentre "):
            item["branch"] = name.removeprefix("Halfords Autocentre ")
            item["brand_wikidata"] = "Q5641894"
        elif name.startswith("Halfords Garage Services "):
            item["name"] = "Halfords Garage Services"
            item["brand"] = "Halfords"
            item["branch"] = name.removeprefix("Halfords Garage Services ")
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        elif name.startswith("National Tyres and Autocare ") or name.endswith(" (National Tyres)"):
            item["branch"] = name.removeprefix("National Tyres and Autocare ").removesuffix(" (National Tyres)")
            item["brand_wikidata"] = "Q6979055"
        elif name.startswith("Halfords Store "):
            item["branch"] = name.removeprefix("Halfords Store ")
            item["brand_wikidata"] = "Q3398786"
        else:
            # 3, a mix of the above.
            item["name"] = name

        yield item
    drop_attributes = {"image"}
