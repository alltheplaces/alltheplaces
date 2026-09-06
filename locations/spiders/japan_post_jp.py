import csv
import math
from io import StringIO
from urllib.parse import urlencode

from chompjs import parse_js_object
from pyproj import Transformer
from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.geo import city_locations, country_iseadgg_centroids
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

    def make_request(self, lat, lon, radius, offset=1, count=900, tempo_count=0, post_count=0, source=""):
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

    def _subdivide(self, lat, lon, radius, source):
        # Replace a truncated circle (center lat/lon, radius m) with 4 smaller
        # circles whose union covers the original. Only used for the city-5.5 pass
        # and only ONE level: children keep source "city-5.5-sub-<quadrant>", which
        # never matches the "city-5.5" trigger, so they are not subdivided again.
        #
        # source is always hyphen-delimited, e.g. grid-24, city-5.5, city-5.5-sub-NW,
        # so it splits cleanly for later analysis.
        #
        # Covering math: the parent disk (radius R) sits inside its bounding square
        # of side 2R. Put one child at each quadrant centre, i.e. offset by R/2 in
        # latitude and R/2 in longitude. The farthest corner of a quadrant from its
        # centre is the half-diagonal sqrt((R/2)^2+(R/2)^2) = R*sqrt(2)/2, so a child
        # of that radius covers its whole quadrant exactly. The 4 quadrants tile the
        # bounding square, therefore union(4 children) = bounding square, which fully
        # contains the parent circle. No point is missed.
        #
        # metre offsets -> degrees: 1 deg latitude ~ 111320 m, and a degree of
        # longitude shrinks by cos(lat), so the R/2 offset in each axis is:
        #   dlat = (R/2) / 111320              (degrees of latitude)
        #   dlon = (R/2) / (111320 * cos(lat)) (degrees of longitude)
        # sub_radius = R*sqrt(2)/2             (child radius, still in metres)
        if radius <= MIN_RADIUS_M:
            self.logger.warning(f"cannot subdivide below {MIN_RADIUS_M}m at {lat},{lon}")
            return
        dlat = (radius / 2) / 111320.0
        dlon = (radius / 2) / (111320.0 * math.cos(math.radians(lat)))
        sub_radius = radius * math.sqrt(2) / 2
        for quadrant, d1, d2 in (
            ("NW", dlat, dlon),
            ("NE", dlat, -dlon),
            ("SW", -dlat, dlon),
            ("SE", -dlat, -dlon),
        ):
            yield self.make_request(lat + d1, lon + d2, sub_radius, source=f"{source}-sub-{quadrant}")

    async def start(self):
        radius_m = RADIUS_KM * 1000
        for lat, lon in country_iseadgg_centroids("JP", RADIUS_KM):
            yield self.make_request(lat, lon, radius_m, source="grid-24")
        for city in city_locations("JP", 200000):
            yield self.make_request(city["latitude"], city["longitude"], 5500, source="city-5.5")

    def parse(self, response, lat, lon, radius, offset, count=900, tempo_count=0, post_count=0, source=""):
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
        rows = list(reader)
        tempo_total = tempo_count + sum(1 for r in rows if r[0] == "TEMPO")
        post_total = post_count + sum(1 for r in rows if r[0] == "POST")

        page = (offset - 1) // count + 1
        self.logger.info(
            f"Query (source={source}, lat={lat}, lon={lon}, radius={radius}, page={page}, offset={offset}, rec={rec_count}, hit={hit_count}, tempo={tempo_total}, post={post_total})"
        )
        if tempo_total >= MAX_ITEMS or post_total >= MAX_ITEMS:
            self.logger.warning(
                f"Maximum number of items returned in one query, consider lowering the radius  (source={source})"
            )
            if source == "city-5.5":
                yield from self._subdivide(lat, lon, radius, source)
            return

        if offset + rec_count < hit_count:
            yield self.make_request(
                lat, lon, radius, offset + rec_count, tempo_count=tempo_total, post_count=post_total, source=source
            )

        for row in rows:
            row_type = row[0]
            ref = row[1]
            lat = row[2]
            lon = row[3]
            # raw lat/lon are Tokyo datum (EPSG:4301). convert to WGS 84 (EPSG:4326)
            wgs84_lat, wgs84_lon = TOKYO_TO_WGS84.transform(float(lat), float(lon))

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
