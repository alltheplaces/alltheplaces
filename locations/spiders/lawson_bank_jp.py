from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.emap import EMapSpider


class LawsonBankJPSpider(EMapSpider):
    name = "lawson_bank_jp"
    map_id = "lbankatm"
    host = "map.lawsonbank.jp"
    item_attributes = {
        "brand": "ローソン銀行",
        "brand_wikidata": "Q11350963",
    }

    def parse_rows(self, rows):
        for row in rows:
            item = Feature()
            item["ref"] = row[0]
            item["website"] = f"https://map.lawsonbank.jp/p/{self.map_id}/dtl/{row[0]}/"
            item["lat"] = row[1]
            item["lon"] = row[2]
            item["branch"] = row[7].removeprefix("ローソン銀行ＡＴＭ　").removesuffix("共同出張所")
            item["addr_full"] = row[8]

            apply_category(Categories.ATM, item)

            yield item
