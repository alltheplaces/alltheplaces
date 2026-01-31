from locations.categories import Categories
from locations.hours import OpeningHours
from locations.storefinders.stockist import StockistSpider

CARPET_COURT = {"brand": "Carpet Court", "brand_wikidata": "Q137908618", "extras": Categories.SHOP_CARPET.value}
CURTAIN_STUDIO = {"brand": "Curtain Studio", "brand_wikidata": "Q137908226", "extras": Categories.SHOP_CURTAIN.value}


class TheInteriorsGroupNZSpider(StockistSpider):
    name = "the_interiors_group_nz"
    key = "map_93wgrpn3"

    def parse_item(self, item, location):
        match location["filters"][0]["name"]:
            case "Carpet Court":
                item.update(CARPET_COURT)
                item["branch"] = item.pop("name").removeprefix("Carpet Court ")
                item["website"] = f"https://carpetcourt.nz{location['custom_fields'][1]['value']}"
            case "Curtain Studio":
                item.update(CURTAIN_STUDIO)
                item["branch"] = item.pop("name").removeprefix("Curtain Studio ")
                item["website"] = f"https://curtainstudio.co.nz{location['custom_fields'][1]['value']}"

        item["opening_hours"] = OpeningHours()
        oh_string = location["custom_fields"][0]["value"].replace("\n ", "\n")

        for lines in oh_string.split("\n"):
            if lines.split(":")[0] in ["Mon-Fri", "Sat", "Sun"]:
                item["opening_hours"].add_ranges_from_string(oh_string)

        yield item
