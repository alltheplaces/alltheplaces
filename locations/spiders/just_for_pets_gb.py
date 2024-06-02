from locations.categories import Categories
from locations.storefinders.storemapper import StoremapperSpider


class JustForPetsGBSpider(StoremapperSpider):
    name = "just_for_pets_gb"
    item_attributes = {"brand": "Just For Pets", "extras": Categories.SHOP_PET.value}
    company_id = "10020"
