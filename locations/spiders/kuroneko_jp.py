import csv
from io import StringIO

from chompjs import parse_js_object
from pyproj import Transformer
from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.geo import city_locations, country_iseadgg_centroids
from locations.items import Feature

MAX_ITEMS = 1640  # determined experimentally
TOKYO_TO_WGS84 = Transformer.from_pipeline("EPSG:15484")
RADIUS_KM = 24
MAP_ID = "yamato01"  # for storefinder


class KuronekoJPSpider(Spider):
    name = "kuroneko_jp"

    def make_request(self, lat, lon, distance, offset=1, count=900):
        return Request(
            f"https://www.e-map.ne.jp/p/{MAP_ID}/zdcemaphttp.cgi?target=http%3A%2F%2F127.0.0.1%2Fcgi%2Fnkyoten.cgi%3F%26cid%3D{MAP_ID}%26pos%3D{offset}%26lat%3D{lat}%26lon%3D{lon}%26knsu%3D{MAX_ITEMS}%26cnt%3D{count}%26hour%3D1%26rad%3D{distance}%26jkn%3D(COL_01%3A1%20OR%20COL_01%3A2%20AND%20((COL_39!%3A002%20AND%20COL_39!%3A001%20AND%20COL_39!%3A003%20AND%20COL_39!%3A418%20AND%20COL_39!%3A436%20AND%20COL_39!%3A101%20AND%20COL_39!%3A171%20AND%20COL_39!%3A207%20AND%20COL_39!%3AZ98%20AND%20COL_39!%3AZ99%20AND%20COL_39!%3A563)%20OR%20(COL_39%20IS%20NULL)))%20AND%20(((COL_01%3A1%20AND%20(COL_10%3AA%20OR%20COL_10%3AB))%20OR%20COL_01%3A2)%20AND%20((COL_39!%3AZ96%20AND%20COL_39!%3AZ97%20AND%20COL_39!%3A003%20AND%20COL_39!%3A207%20AND%20COL_39!%3AZ98%20AND%20COL_39!%3AZ99)%20OR%20COL_39%3A%40%40NULL%40%40))&zdccnt=1",
            cb_kwargs={"lat": lat, "lon": lon, "offset": offset},
        )

    async def start(self):
        radius_m = RADIUS_KM * 1000
        for lat, lon in country_iseadgg_centroids("JP", RADIUS_KM):
            yield self.make_request(lat, lon, radius_m)

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
            if any(
                i in row[6] for i in ["ツルハ", "福太郎", "イレブン", "ウォンツ", "B＆D", "Ｂ＆Ｄ"]
            ):  # skip Tsuruha Drug locations
                continue
            item = Feature()
            item["ref"] = row[0]
            item["website"] = f"https://www.e-map.ne.jp/p/{MAP_ID}/dtl/{row[0]}/"
            lat = float(row[1])
            lon = float(row[2])
            wgs84_lat, wgs84_lon = TOKYO_TO_WGS84.transform(lat, lon)
            item["lat"] = wgs84_lat
            item["lon"] = wgs84_lon
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
