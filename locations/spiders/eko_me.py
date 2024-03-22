from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class EkoMESpider(LighthouseSpider):
    name = "eko_me"
    item_attributes = {"brand": "EKO", "brand_wikidata": "Q111604689", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.jugopetrol.co.me"]
    start_urls = ["https://www.jugopetrol.co.me/stanice/prona-i-stanicu/"]
