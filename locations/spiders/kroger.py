import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT

BRANDS = {
    "https://www.bakersplus.com/": {"brand": "Baker's", "brand_wikidata": "Q4849080"},
    "https://www.citymarket.com/": {"brand": "City Market", "brand_wikidata": "Q5123299"},
    "https://www.dillons.com/": {"brand": "Dillons", "brand_wikidata": "Q5276954"},
    "https://www.food4less.com/": {"brand": "Food 4 Less", "brand_wikidata": "Q5465282"},
    "https://www.foodsco.net/": {"brand": "Foods Co", "brand_wikidata": "Q5465282"},
    "https://www.fredmeyer.com/": {"brand": "Fred Meyer", "brand_wikidata": "Q5495932"},
    "https://www.frysfood.com/": {"brand": "Fry's Food Stores", "brand_wikidata": "Q5506547"},
    "https://www.gerbes.com/": {"brand": "Gerbes", "brand_wikidata": "Q5276954"},
    "https://www.jaycfoods.com/": {"brand": "JayC", "brand_wikidata": "Q6166302"},
    "https://www.kingsoopers.com/": {"brand": "King Soopers", "brand_wikidata": "Q6412065"},
    "https://www.kroger.com/": {"brand": "Kroger", "brand_wikidata": "Q153417"},
    "https://www.marianos.com/": {"brand": "Mariano's Fresh Market", "brand_wikidata": "Q55622168"},
    "https://www.metromarket.net/": {"brand": "Metro Market", "brand_wikidata": "Q7371288"},
    "https://www.pay-less.com/": {"brand": "Pay Less", "brand_wikidata": "Q7156587"},
    "https://www.picknsave.com/": {"brand": "Pick 'n Save", "brand_wikidata": "Q7371288"},
    "https://www.qfc.com/": {"brand": "QFC", "brand_wikidata": "Q7265425"},
    "https://www.ralphs.com/": {"brand": "Ralphs", "brand_wikidata": "Q3929820"},
    "https://www.smithsfoodanddrug.com/": {"brand": "Smith's", "brand_wikidata": "Q7544856"},
}


class KrogerSpider(SitemapSpider, StructuredDataSpider):
    name = "kroger"
    sitemap_urls = [f"{brand}storelocator-sitemap.xml" for brand in BRANDS.keys()]
    sitemap_rules = [("/stores/grocery/", "parse_sd")]
    custom_settings = {"AUTOTHROTTLE_ENABLED": True, "USER_AGENT": BROWSER_DEFAULT}

    def pre_process_data(self, ld_data, **kwargs):
        if phone := ld_data.get("telephone"):
            if isinstance(phone, dict):
                ld_data["telephone"] = phone.get("original")

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"\"lat\":(-?\d+\.\d+),\"lng\":(-?\d+\.\d+)", response.text):
            item["lat"], item["lon"] = m.groups()

        for url, brand in BRANDS.items():
            if response.url.startswith(url):
                item.update(brand)
                break

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
