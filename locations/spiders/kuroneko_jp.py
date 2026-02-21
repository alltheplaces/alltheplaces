import csv
from io import StringIO

from chompjs import parse_js_object
from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.items import Feature

BRANDS = {
    "001": ("ファミリーマート", "Q11247682"),
    "002": ("セブン-イレブン", "Q259340"),
    "101": ("ポプラ", "Q7229380"),
    "171": ("ポプラ", "Q7229380"),
    "418": ("NewDays", "Q11234763"),
    "436": ("デイリーヤマザキ", "Q5209392"),
    "YTC": ("ヤマト運輸", "Q6584353"),
}
MAX_ITEMS = 1640  # determined experimentally
RADIUS_KM = 24
MAP_ID = "yamato01"  # for storefinder


class KuronekoJPSpider(Spider):
    name = "kuroneko_jp"

    def make_request(self, lat, lon, offset=1, count=900):
        radius_m = RADIUS_KM * 1000
        return Request(
            f"https://www.e-map.ne.jp/p/{MAP_ID}/zdcemaphttp.cgi?target=http%3A%2F%2F127.0.0.1%2Fcgi%2Fnkyoten.cgi%3F%26cid%3D{MAP_ID}%26pos%3D{offset}%26lat%3D{lat}%26lon%3D{lon}%26knsu%3D{MAX_ITEMS}%26cnt%3D{count}%26hour%3D1%26rad%3D{radius_m}&zdccnt=1",
            cb_kwargs={"lat": lat, "lon": lon, "offset": offset},
        )

    async def start(self):
        for lat, lon in country_iseadgg_centroids("JP", RADIUS_KM):
            yield self.make_request(lat, lon)

    def parse(self, response, lat, lon, offset):
        # response is an EUC-encoded JS file that looks like
        #   ZdcEmapHttpResult[1] = '...';
        # where the string body is a TSV
        js_body = response.body.decode("euc-jp")
        # chompjs sees the array index as an array itself, so get just the string itself:
        js_str = js_body[js_body.find("'") : js_body.rfind("'") + 1]
        # For some reason, neither Python json nor chompjs like just the string on its own, so wrap it in an array
        js_ls = f"[{js_str}]"
        (tsv_str,) = parse_js_object(js_ls)
        reader = csv.reader(StringIO(tsv_str), delimiter="\t")
        ret_code, rec_count, hit_count = map(int, next(reader))
        assert rec_count <= hit_count, (rec_count, hit_count)
        if hit_count >= MAX_ITEMS:
            self.logger.warning("Maximum number of items returned in one query, consider lowering the radius")
        if rec_count >= hit_count:
            yield self.make_request(lat, lon, offset + rec_count)
        for row in reader:
            item = Feature()
            item["ref"] = row[0]
            item["website"] = f"https://www.e-map.ne.jp/p/{MAP_ID}/dtl/{row[0]}/"
            item["lat"] = row[1]
            item["lon"] = row[2]
            if row[3] == "YTC":
                apply_category(Categories.POST_OFFICE, item)
            elif row[3] == "563":
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                apply_category(Categories.POST_PARTNER, item)
                item["extras"]["post_office:service_provider"] = "ヤマト運輸"

            item["brand"], item["brand_wikidata"] = BRANDS.get(row[3], (None, None))
            item["name"] = row[6]
            item["addr_full"] = row[7]
            item["phone"] = row[16]

            # row 35-42 =1 is days the place is closed. 35-41 is Mon-Sun, 42 is holidays. row 43 =1 means open every day.

            if row[44] == "1":
                item["opening_hours"] = "24/7"

            yield item
