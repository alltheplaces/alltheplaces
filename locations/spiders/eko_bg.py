from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class EkoBGSpider(LighthouseSpider):
    name = "eko_bg"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q111603199", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.eko.bg"]
    start_urls = ["https://www.eko.bg/stations/karta-na-obektite/"]
