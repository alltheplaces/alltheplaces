from locations.categories import Categories
from locations.spiders.penneys_ie import PenneysIESpider


class PrimarkGBSpider(PenneysIESpider):
    name = "primark_gb"
    item_attributes = {"brand": "Primark", "brand_wikidata": "Q137023", "extras": Categories.SHOP_CLOTHES.value}
    locale = "en-gb"
