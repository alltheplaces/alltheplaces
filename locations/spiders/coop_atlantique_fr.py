import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CoopAtlantiqueFRSpider(scrapy.Spider):
    name = "coop_atlantique_fr"
    item_attributes = {"brand": "Coop Atlantique", "brand_wikidata": "Q2996560"}
    start_urls = ["https://www.coop-atlantique.fr/nos-activites/nos-magasins/"]

    def parse(self, response, **kwargs):
        stores = chompjs.parse_js_object(response.xpath('//*[@id="arrayMagasin"]/@value').get())
        for store in stores:
            brand_name = store.get("nomEnseigne", "").lower()
            if brand_name != "coop":
                continue
            item = DictParser.parse(store)
            item["branch"] = store.get("nomMag").replace("Utile ", "").replace("Coop ", "")
            item["street_address"] = merge_address_lines(
                [store.get("adresse"), store.get("adresse2"), store.get("adresse3")]
            )
            item["city"] = store.get("ville")
            item["postcode"] = store.get("cp")
            item["phone"] = store.get("telFixe")
            item["lat"] = store.get("geox")
            item["lon"] = store.get("geoy")
            apply_category(Categories.SHOP_CONVENIENCE, item)
            yield item
