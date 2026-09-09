from scrapy.spiders import SitemapSpider
import chompjs

from locations.structured_data_spider import StructuredDataSpider
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.hours import OpeningHours, DAYS_FR, DELIMITERS_FR, CLOSED_FR
from locations.dict_parser import DictParser


class AutodistributionFRSpider(SitemapSpider):
    name = "autodistribution_fr"
    item_attributes = {
        "brand": "Autodistribution",
        "brand_wikidata": "Q139825482",
    }
    sitemap_urls = ["https://www.autodistribution.fr/sitemap.xml"]
    sitemap_rules = [(r"autodistribution.fr/magasins-pieces-auto/[^/]+", "process_item")]

    def process_item(self, response):

        script = response.xpath('//script[contains(text(), "schedule")]/text()').get()
        if not script:
            return
        slug = response.url.rstrip("/").split("/")[-1].split("?")[0]
        payload = chompjs.parse_js_object(script.replace("&q;", '"'))
        key = f"G.json.https://backend.production.gcp.autodistribution.fr/api/shop/{slug}?"
        if key not in payload:
            return
        data = payload[key]["body"]
        
        item = DictParser.parse(data)
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        item["country"] = "FR"
        
        item["branch"] = item.pop("name", "").removeprefix("autodistribution ")

        item["street_address"] = item.pop("addr_full","")
        item["email"] = data.pop("mail","")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(data["schedule"].replace("et"," ").split("Atelier")[0], DAYS_FR, delimiters=DELIMITERS_FR, closed=CLOSED_FR)
    
        yield item
