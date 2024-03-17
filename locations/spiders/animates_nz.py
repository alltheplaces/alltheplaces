from locations.categories import Categories
from locations.storefinders.aheadworks import AheadworksSpider


class AnimatesNZSpider(AheadworksSpider):
    name = "animates_nz"
    allowed_domains = [
        "www.animates.co.nz",
    ]
    start_urls = ["https://www.animates.co.nz/store-finder"]
    item_attributes = {"brand": "Animates", "brand_wikidata": "Q110299350", "extras": Categories.SHOP_PET.value}
