from pyproj import Transformer

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.emap import EMapSpider


class KuronekoJPSpider(EMapSpider):
    name = "kuroneko_jp"
    map_id = "yamato01"

    def make_request(self, lat, lon, radius, offset=1, count=900):
        return super().make_request(
            lat,
            lon,
            radius,
            offset,
            count,
            extra_params={
                "jkn": "(COL_01:1 OR COL_01:2 AND ((COL_39!:002 AND COL_39!:001 AND COL_39!:003 AND COL_39!:418 AND "
                "COL_39!:436 AND COL_39!:101 AND COL_39!:171 AND COL_39!:207 AND COL_39!:Z98 AND COL_39!:Z99 "
                "AND COL_39!:563) OR (COL_39 IS NULL))) AND (((COL_01:1 AND (COL_10:A OR COL_10:B)) OR "
                "COL_01:2) AND ((COL_39!:Z96 AND COL_39!:Z97 AND COL_39!:003 AND COL_39!:207 AND COL_39!:Z98 "
                "AND COL_39!:Z99) OR COL_39:@@NULL@@))"
            },
        )

    async def start(self):
        self.transformer = Transformer.from_pipeline("EPSG:15484")
        async for req in super().start():
            yield req

    def parse_row(self, row):
        if any(
            i in row[6] for i in ["ツルハ", "福太郎", "イレブン", "ウォンツ", "B＆D", "Ｂ＆D"]
        ):  # skip Tsuruha Drug locations
            return
        item = Feature()
        item["ref"] = row[0]
        item["website"] = f"https://www.e-map.ne.jp/p/{self.map_id}/dtl/{row[0]}/"
        lat = float(row[1])
        lon = float(row[2])
        item["lat"], item["lon"] = self.transformer.transform(lat, lon)
        if row[3] == "YTC":
            apply_category(Categories.POST_OFFICE, item)
            item["branch"] = row[6]
            item["name"] = item["brand"] = "ヤマト運輸"
            item["brand_wikidata"] = "Q6584353"
        else:
            item["name"] = row[6]
            apply_category(Categories.GENERIC_POI, item)
            item.set_tag("post_office", "post_partner")
            item.set_tag("post_office:service_provider", "ヤマト運輸")

        item["addr_full"] = row[7]
        item["phone"] = row[16]

        # row 35-42 =1 is days the place is closed. 35-41 is Mon-Sun, 42 is holidays. row 43 =1 means open every day.
        if row[44] == "1":
            item["opening_hours"] = "24/7"

        yield item
