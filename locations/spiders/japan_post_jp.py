import csv
import math
from io import StringIO
from urllib.parse import urlencode

from chompjs import parse_js_object
from pyproj import Transformer
from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.geo import KILOMETERS_PER_DEGREE_LATITUDE, country_iseadgg_centroids
from locations.items import Feature

# determined experimentally. per-type cap (TEMPO/POST). a type reaching this is truncated
MAX_ITEMS = 1640

# Tokyo (EPSG:4301) -> WGS 84 (EPSG:4326) via EPSG:15484 (Tokyo to WGS 84 (108)).
TOKYO_TO_WGS84 = Transformer.from_pipeline("EPSG:15484")
RADIUS_KM = 24
MIN_RADIUS_M = 1000
MAP_ID = "search"


class JapanPostJPSpider(Spider):
    name = "japan_post_jp"

    def make_request(
        self,
        lat: float,
        lon: float,
        radius: float,
        offset: int = 1,
        count: int = 900,
        tempo_count: int = 0,
        post_count: int = 0,
        source: str = "",
    ):
        params = {
            "cid": MAP_ID,
            "postcid": "searchPO",
            # include TEMPO (post offices + ATMs + kanpo insurance)
            "search_tempo": "1",
            # include POST (postboxes)
            "search_post": "1",
            "opt": "search",
            # starting row (1-based). increased by rec_count to paginate
            "pos": offset,
            # page size (rows per response). does not limit the total
            "cnt": count,
            "enc": "EUC",
            "lat": lat,
            "lon": lon,
            # cap on TEMPO rows for this whole query
            "knsu": MAX_ITEMS,
            # cap on POST rows for this whole query
            "postknsu": MAX_ITEMS,
            # search radius in metres
            "rad": radius,
            "hour": 1,
        }
        target = urlencode({"target": f"http://127.0.0.1/cgi/nkyoten.cgi?{urlencode(params)}"})
        url = f"https://map.japanpost.jp/p/{MAP_ID}/zdcemaphttp.cgi?{target}&zdccnt=1&enc=EUC"
        return Request(
            url,
            cb_kwargs={
                "lat": lat,
                "lon": lon,
                "radius": radius,
                "offset": offset,
                "count": count,
                "tempo_count": tempo_count,
                "post_count": post_count,
                "source": source,
            },
        )

    def _child_circles(
        self, lat_parent: float, lon_parent: float, radius_parent: float
    ) -> list[tuple[float, float, float, str]]:
        """
        Return the 4 child circles to fully cover a parent circle of the given radius.

        Each child is offset from the parent center by half the parent radius in latitude and in
        longitude, and its radius is the distance to the half-diagonal. The four quadrants tile the
        square around the parent circle, so the children cover it completely.
        """
        lat_child = (radius_parent / 2 / 1000) / KILOMETERS_PER_DEGREE_LATITUDE
        lon_child = (radius_parent / 2 / 1000) / (KILOMETERS_PER_DEGREE_LATITUDE * math.cos(math.radians(lat_parent)))
        radius_child = radius_parent * math.sqrt(2) / 2
        return [
            (lat_parent + lat_child, lon_parent + lon_child, radius_child, "NW"),
            (lat_parent + lat_child, lon_parent - lon_child, radius_child, "NE"),
            (lat_parent - lat_child, lon_parent + lon_child, radius_child, "SW"),
            (lat_parent - lat_child, lon_parent - lon_child, radius_child, "SE"),
        ]

    def _subdivide(self, lat_parent: float, lon_parent: float, radius_parent: float, source: str):
        # Split a truncated circle into 4 children and issue their queries.
        # Children keep source "<parent>-<quadrant>" and are recursively subdivided until no child is truncated.
        if radius_parent <= MIN_RADIUS_M:
            self.logger.warning(f"cannot subdivide below {MIN_RADIUS_M}m at {lat_parent},{lon_parent}")
            return
        for center_child_lat, center_child_lon, radius_child, quadrant in self._child_circles(
            lat_parent, lon_parent, radius_parent
        ):
            yield self.make_request(center_child_lat, center_child_lon, radius_child, source=f"{source}-{quadrant}")

    async def start(self):
        radius_m = RADIUS_KM * 1000
        for i, (lat, lon) in enumerate(country_iseadgg_centroids("JP", RADIUS_KM)):
            yield self.make_request(lat, lon, radius_m, source=f"grid-{i}")

    def parse(
        self,
        response: Response,
        lat: float,
        lon: float,
        radius: float,
        offset: int,
        count=900,
        tempo_count=0,
        post_count=0,
        source="",
    ):
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
        _, rec_count, hit_count = map(int, next(reader))
        assert rec_count <= hit_count, (rec_count, hit_count)
        rows = list(reader)
        tempo_total = tempo_count + sum(1 for r in rows if r[0] == "TEMPO")
        post_total = post_count + sum(1 for r in rows if r[0] == "POST")

        page = (offset - 1) // count + 1
        self.logger.info(
            f"Query (source={source}, lat={lat}, lon={lon}, radius={radius}, page={page}, offset={offset}, rec={rec_count}, hit={hit_count}, tempo={tempo_total}, post={post_total})"
        )
        if tempo_total >= MAX_ITEMS or post_total >= MAX_ITEMS:
            self.logger.info(
                f"Maximum number of items {MAX_ITEMS} returned in one query, subdividing into small circles (source={source})"
            )
            yield from self._subdivide(lat, lon, radius, source)
            return

        if offset + rec_count < hit_count:
            yield self.make_request(
                lat, lon, radius, offset + rec_count, tempo_count=tempo_total, post_count=post_total, source=source
            )

        for row in rows:
            row_type = row[0]
            ref = row[1]
            lat = float(row[2])
            lon = float(row[3])
            # raw lat/lon are Tokyo datum (EPSG:4301). convert to WGS 84 (EPSG:4326)
            wgs84_lat, wgs84_lon = TOKYO_TO_WGS84.transform(lat, lon)

            if row_type == "POST":
                postcode = row[21]
                addr_full = row[7]
                item = Feature()
                item["ref"] = ref
                # post detail page is not accessible without `?post=1`
                item["website"] = f"https://map.japanpost.jp/p/{MAP_ID}/dtl/{ref}/?post=1"
                item["lat"] = wgs84_lat
                item["lon"] = wgs84_lon
                item["postcode"] = postcode
                item["addr_full"] = addr_full

                apply_category(Categories.POST_BOX, item)
                item["operator_wikidata"] = "Q11509260"
                yield item
                continue

            # col [icon] is an icon_id (marker image) that selects the category:
            #   01, 02          = post office
            #   03,04,06,07,08  = ATM
            #   05              = Japan Post kanpo Insurance
            #   99              = search-center pin, not a real location
            icon = row[4]
            if icon == "99":
                continue

            name = row[7]
            postcode = row[13]
            addr_full = row[14]

            item = Feature()
            item["ref"] = ref
            item["website"] = f"https://map.japanpost.jp/p/{MAP_ID}/dtl/{ref}/"
            item["lat"] = wgs84_lat
            item["lon"] = wgs84_lon
            item["postcode"] = postcode
            item["addr_full"] = addr_full
            if icon in ("01", "02"):
                apply_category(Categories.POST_OFFICE, item)
                item.update({"brand": "日本郵便", "brand_wikidata": "Q11509260"})
                item["name"] = name
            elif icon == "05":
                apply_category(Categories.OFFICE_INSURANCE, item)
                item.update({"brand": "かんぽ生命保険", "brand_wikidata": "Q6157781"})
                item["name"] = name
            else:
                apply_category(Categories.ATM, item)
                item.update({"brand": "ゆうちょ銀行", "brand_wikidata": "Q907103"})
                item["branch"] = name.removesuffix("出張所")

            yield item
