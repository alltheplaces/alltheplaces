from locations.categories import Categories
from locations.storefinders.lighthouse import LighthouseSpider


class OktaMKSpider(LighthouseSpider):
    name = "okta_mk"
    item_attributes = {"brand": "OKTA", "brand_wikidata": "Q3350105", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["www.okta-elpe.com"]
    start_urls = ["https://www.okta-elpe.com/service-stations/find-a-station/"]
