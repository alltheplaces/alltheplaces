import math
import re
import unicodedata
from typing import AsyncIterator, Iterable
from urllib.parse import urlparse, urlunparse

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, Sport, add_sport, apply_category
from locations.items import Feature
from locations.licenses import Licenses


class LipasFISpider(Spider):
    """Finnish national sports-facility database (LIPAS), University of Jyväskylä.

    Feed: GET https://api.lipas.fi/v2/sports-sites (V2, current API; V1 is
    frozen legacy with a divergent taxonomy). Default status filter keeps only
    venues in use (active + temporarily out of service); permanently closed,
    planned and incorrect records stay out. Scale Oct 2026: ~49.4k records in
    scope (active + temporarily out of service), of which ~9.1k linear routes and ~0.2k maintenance buildings are
    deliberately excluded below, yielding ~40.2k venues (points plus polygon
    centroids).
    """

    name = "lipas_fi"
    allowed_domains = ["api.lipas.fi"]

    # API contents CC BY 4.0, see https://api.lipas.fi/
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Contains LIPAS data, University of Jyväskylä",
        "attribution:website": "https://www.lipas.fi/",
    }

    api_base_url = "https://api.lipas.fi/v2"
    page_size = 100

    # Geometry types that can yield a usable point; anything else (including a
    # missing type) is counted and skipped rather than silently ignored.
    KNOWN_GEOMETRIES = frozenset({"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon"})

    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    # V2 type-code -> (category, sport). None means deliberately excluded, and a
    # missing code (future taxonomy addition) falls back to generic, never drop.
    # Counts are active + temporarily-out-of-service records as of Oct 2026.
    TYPE_MAP = {
        101: (Categories.LEISURE_PARK, None),  # Neighbourhood park (285, polygon)
        103: (Categories.LEISURE_PARK, None),  # Outdoor area (244, polygon)
        106: (Categories.LEISURE_PARK, None),  # Multi-use recreational forest (14, polygon)
        107: (Categories.CARAVAN_SITE, None),  # Tourist services area (14, polygon)
        109: (Categories.LEISURE_NATURE_RESERVE, None),  # National hiking area (5, polygon)
        110: (Categories.LEISURE_NATURE_RESERVE, None),  # Wilderness area (13, polygon)
        111: (Categories.LEISURE_NATURE_RESERVE, None),  # National park (41, polygon)
        112: (Categories.LEISURE_NATURE_RESERVE, None),  # Nature conservation area (79, polygon)
        113: (Categories.LEISURE_FISHING, None),  # Fishing area (52, polygon)
        201: (Categories.LEISURE_FISHING, None),  # Fishing area (328)
        202: (Categories.TOURISM_CAMP_SITE, None),  # Camping (64)
        203: (Categories.MARINA, None),  # Boating services (1084)
        204: (Categories.TOURISM_VIEWPOINT, None),  # Nature observation tower (793)
        206: (Categories.TOURISM_PICNIC_SITE, None),  # Cooking facilities (656)
        207: (Categories.TOURISM_INFORMATION, None),  # Info (951)
        301: (Categories.SHELTER, None),  # Lean-to/kota (2993)
        302: (Categories.TOURISM_WILDERNESS_HUT, None),  # Hut (176)
        304: (Categories.TOURISM_WILDERNESS_HUT, None),  # Outdoor/ski lodge (81)
        1110: (Categories.LEISURE_SPORTS_CENTRE, None),  # Sports park (114, polygon)
        1120: (Categories.LEISURE_SPORTS_CENTRE, None),  # Neighbourhood sports area (1632)
        1130: (Categories.LEISURE_FITNESS_STATION, None),  # Street workout park (1862)
        1140: (Categories.LEISURE_PITCH, Sport.PARKOUR),  # Parkour area (102)
        1150: (Categories.LEISURE_PITCH, Sport.SKATEBOARD),  # Skate/roller rink (360)
        1160: (Categories.LEISURE_TRACK, Sport.CYCLING),  # Cycling area (121)
        1170: (Categories.LEISURE_TRACK, Sport.CYCLING),  # Velodrome (7)
        1180: (Categories.LEISURE_DISC_GOLF_COURSE, None),  # Disc golf course (1057)
        1190: (Categories.GENERIC_POI, None),  # Sledding hill, no sledding tag (95)
        1210: (Categories.LEISURE_PITCH, Sport.ATHLETICS),  # Athletics training area (513)
        1220: (Categories.LEISURE_PITCH, Sport.ATHLETICS),  # Athletics field (265)
        1310: (Categories.LEISURE_PITCH, Sport.BASKETBALL),  # Basketball court (597)
        1320: (Categories.LEISURE_PITCH, Sport.VOLLEYBALL),  # Volleyball court (209)
        1330: (Categories.LEISURE_PITCH, Sport.BEACH_VOLLEYBALL),  # Beach volleyball (989)
        1340: (Categories.LEISURE_PITCH, None),  # Ball field, sport unspecified (5212)
        1350: (Categories.LEISURE_PITCH, Sport.SOCCER),  # Football stadium (30)
        1360: (Categories.LEISURE_PITCH, Sport.BASEBALL),  # Baseball field (127)
        1370: (Categories.LEISURE_PITCH, Sport.TENNIS),  # Tennis court area (1416)
        1380: (Categories.LEISURE_PITCH, None),  # Roller hockey field (11)
        1390: (Categories.LEISURE_PITCH, Sport.PADEL),  # Padel court area (323)
        1395: (Categories.LEISURE_PITCH, Sport.TABLE_TENNIS),  # Outdoor table tennis (51)
        1510: (Categories.LEISURE_ICE_RINK, Sport.ICE_SKATING),  # Frozen open-air rink (89)
        1520: (Categories.LEISURE_ICE_RINK, Sport.ICE_SKATING),  # Ice-skating field (1829)
        1530: (Categories.LEISURE_PITCH, Sport.ICE_HOCKEY),  # Rink/kaukalo (1331)
        1540: (Categories.LEISURE_ICE_RINK, Sport.ICE_SKATING),  # Speed-skating track (10)
        1550: (Categories.LEISURE_ICE_RINK, Sport.ICE_SKATING),  # Ice-skating route (46)
        1560: (Categories.LEISURE_ICE_RINK, Sport.ICE_SKATING),  # Downhill skating track (1)
        1610: (Categories.LEISURE_GOLF_COURSE, None),  # Golf training area (43)
        1630: (Categories.LEISURE_SPORTS_HALL, None),  # Indoor golf training hall (28)
        1640: (Categories.LEISURE_MINIATURE_GOLF, None),  # Minigolf course (49)
        1650: (Categories.LEISURE_GOLF_COURSE, None),  # Golf course (166, polygon)
        2110: (Categories.GYM, None),  # Fitness centre (519)
        2120: (Categories.GYM, None),  # Gym (1431)
        2130: (Categories.GYM, None),  # Weight training hall (164)
        2140: (Categories.LEISURE_SPORTS_CENTRE, Sport.MARTIAL_ARTS),  # Martial arts hall (263)
        2150: (Categories.LEISURE_SPORTS_HALL, None),  # Gymnastics hall (3030)
        2210: (Categories.LEISURE_SPORTS_HALL, None),  # Sports hall (491)
        2220: (Categories.LEISURE_SPORTS_CENTRE, None),  # Multipurpose hall/arena (35)
        2225: (Categories.LEISURE_INDOOR_PLAY, None),  # Indoor playground (26)
        2230: (Categories.LEISURE_SPORTS_HALL, Sport.SOCCER),  # Football hall (86)
        2240: (Categories.LEISURE_SPORTS_HALL, Sport.FLOORBALL),  # Floorball hall (44)
        2250: (Categories.LEISURE_SPORTS_CENTRE, Sport.SKATEBOARD),  # Indoor skatepark (21)
        2260: (Categories.LEISURE_SPORTS_HALL, Sport.BADMINTON),  # Badminton hall (56)
        2270: (Categories.LEISURE_SPORTS_HALL, None),  # Squash hall (59)
        2280: (Categories.LEISURE_SPORTS_HALL, Sport.TENNIS),  # Tennis hall (103)
        2290: (Categories.LEISURE_SPORTS_HALL, None),  # Petanque hall (13)
        2295: (Categories.LEISURE_SPORTS_HALL, Sport.PADEL),  # Padel hall (127)
        2310: (Categories.LEISURE_SPORTS_HALL, Sport.ATHLETICS),  # Indoor athletics venue (86)
        2320: (Categories.LEISURE_SPORTS_HALL, None),  # Artistic gymnastics facility (68)
        2330: (Categories.LEISURE_SPORTS_HALL, Sport.TABLE_TENNIS),  # Table tennis venue (43)
        2340: (Categories.LEISURE_SPORTS_HALL, None),  # Fencing venue (13)
        2350: (Categories.LEISURE_DANCE, None),  # Dance studio (230)
        2360: (Categories.LEISURE_SPORTS_CENTRE, None),  # Indoor shooting range (121)
        2370: (Categories.LEISURE_SPORTS_CENTRE, Sport.CLIMBING),  # Indoor climbing wall (114)
        2380: (Categories.LEISURE_SPORTS_CENTRE, Sport.PARKOUR),  # Parkour hall (11)
        2510: (Categories.LEISURE_ICE_RINK, None),  # Training ice arena (76)
        2520: (Categories.LEISURE_ICE_RINK, None),  # Competition ice arena (164)
        2530: (Categories.LEISURE_ICE_RINK, None),  # Speed-skating hall (0)
        2610: (Categories.LEISURE_BOWLING_ALLEY, None),  # Bowling alley (133)
        2620: (Categories.LEISURE_SPORTS_HALL, None),  # Billiard hall (112)
        3110: (Categories.LEISURE_SPORTS_CENTRE, Sport.SWIMMING),  # Indoor swimming pool (192)
        3120: (Categories.LEISURE_SPORTS_HALL, Sport.SWIMMING),  # Swimming pool (60)
        3130: (Categories.GENERIC_POI, None),  # Spa, no spa tag in categories (55)
        3210: (Categories.LEISURE_SPORTS_CENTRE, Sport.SWIMMING),  # Open-air pool (35)
        3220: (Categories.NATURAL_BEACH, None),  # Public beach (496)
        3230: (Categories.LEISURE_SWIMMING_AREA, None),  # Swimming site (1711)
        3240: (Categories.LEISURE_SWIMMING_AREA, None),  # Winter swimming area (377)
        3250: (Categories.LEISURE_SPORTS_CENTRE, None),  # Water sports center (11)
        4110: (Categories.LEISURE_SPORTS_CENTRE, None),  # Ski slopes/resort (90)
        4210: (Categories.LEISURE_ICE_RINK, None),  # Curling sheet (11)
        4220: (Categories.LEISURE_SPORTS_HALL, None),  # Ski tunnel (5)
        4230: (Categories.LEISURE_SPORTS_HALL, None),  # Snowboarding tunnel (0)
        4240: (Categories.LEISURE_SPORTS_HALL, None),  # Downhill skiing hall (0)
        4320: (Categories.GENERIC_POI, None),  # Ski jumping hill, no ski-jump tag (71)
        4401: None,  # Jogging track, linear route excluded (1594)
        4402: None,  # Ski track, linear route excluded (3126)
        4403: None,  # Walking route, linear route excluded (548)
        4404: None,  # Nature trail, linear route excluded (866)
        4405: None,  # Hiking route, linear route excluded (890)
        4406: None,  # Multi-use trail, linear route excluded (86)
        4407: None,  # Roller ski track, linear route excluded (11)
        4411: None,  # Cross-country biking route, linear excluded (307)
        4412: None,  # Biking route, linear route excluded (468)
        4421: None,  # Official snowmobile route, linear excluded (188)
        4422: None,  # Unofficial snowmobile route, linear excluded (606)
        4430: None,  # Horse track, linear route excluded (26)
        4440: None,  # Dog skijoring track, linear excluded (84)
        4441: None,  # Dog sledding route, linear excluded (13)
        4451: None,  # Canoe route, linear route excluded (222)
        4452: None,  # Water route, linear route excluded (27)
        4510: (Categories.GENERIC_POI, None),  # Orienteering area: forest polygons with no POI tag (104)
        4610: (Categories.GENERIC_POI, None),  # Biathlon training area, no biathlon tag (37)
        4620: (Categories.LEISURE_SPORTS_CENTRE, None),  # Biathlon centre (36)
        4630: (Categories.LEISURE_SPORTS_CENTRE, None),  # Cross-country skiing centre (118)
        4640: (Categories.LEISURE_SPORTS_CENTRE, None),  # Cross-country ski park (60)
        4710: (Categories.LEISURE_PITCH, Sport.CLIMBING),  # Open-air climbing venue (48)
        4720: (Categories.LEISURE_PITCH, Sport.CLIMBING),  # Climbing rock (13)
        4810: (Categories.LEISURE_SPORTS_CENTRE, None),  # Open-air shooting range (456)
        4820: (Categories.LEISURE_SPORTS_CENTRE, None),  # Shooting sports centre (44)
        4830: (Categories.LEISURE_PITCH, Sport.ARCHERY),  # Archery range (76)
        4840: (Categories.GENERIC_POI, None),  # Field archery course, woodland no POI tag (12)
        5110: (Categories.LEISURE_SPORTS_CENTRE, None),  # Rowing stadium (8)
        5120: (Categories.GENERIC_POI, None),  # Sailing area, water area no POI tag (25)
        5130: (Categories.GENERIC_POI, None),  # Motor boat sports area, no tag (0)
        5140: (Categories.GENERIC_POI, None),  # Water ski area, no POI tag (3)
        5150: (Categories.LEISURE_SPORTS_CENTRE, None),  # Canoeing centre (3)
        5160: (Categories.LEISURE_SPORTS_HALL, None),  # Indoor rowing/canoe training (4)
        5210: (Categories.GENERIC_POI, None),  # Sport aviation area, no aerodrome tag (61)
        5310: (Categories.LEISURE_SPORTS_CENTRE, None),  # Motor sports centre (22)
        5320: (Categories.LEISURE_TRACK, None),  # Motorcycling area (83)
        5330: (Categories.LEISURE_TRACK, None),  # Formula race track (6)
        5340: (Categories.LEISURE_TRACK, Sport.KARTING),  # Kart circuit (56)
        5350: (Categories.LEISURE_TRACK, None),  # Dragstrip (2)
        5360: (Categories.LEISURE_TRACK, None),  # Folk racing/rallycross track (46)
        5370: (Categories.LEISURE_TRACK, None),  # Ice speedway track (1)
        6110: (Categories.LEISURE_PITCH, Sport.EQUESTRIAN),  # Equestrian field (769)
        6120: (Categories.LEISURE_SPORTS_CENTRE, Sport.EQUESTRIAN),  # Riding manege (398)
        6130: (Categories.LEISURE_PITCH, Sport.EQUESTRIAN),  # Show jumping field (24)
        6140: (Categories.LEISURE_TRACK, Sport.EQUESTRIAN),  # Horse racing track (97)
        6150: (Categories.LEISURE_TRACK, Sport.EQUESTRIAN),  # Oval track (13)
        6210: (Categories.LEISURE_DOG_PARK, None),  # Dog sports area (120)
        6220: (Categories.LEISURE_SPORTS_HALL, None),  # Dog sports hall, indoor (109)
        7000: None,  # Maintenance building, back-office not a venue (176)
    }

    # Folded V2 type names (fi), from /v2/sports-site-categories Oct 2026.
    # ASCII-folded so the source file stays mojibake-proof; compared against
    # equally folded name tails only, never emitted.
    TYPE_FI = {
        101: "lahi-/ulkoilupuisto",
        103: "ulkoilu-/virkistysalue",
        106: "monikayttoalue tai virkistysmetsa, jossa on virkistyspalveluita",
        107: "matkailupalveluiden alue",
        109: "valtion retkeilyalue",
        110: "eramaa-alue",
        111: "kansallispuisto",
        112: "muu luonnonsuojelualue, jolla on virkistyspalveluita",
        113: "kalastuskohde (alue)",
        201: "kalastuskohde (piste)",
        202: "telttailu ja leiriytyminen",
        203: "veneilyn palvelupaikka",
        204: "luontotorni",
        206: "ruoanlaitto-/tulentekopaikka",
        207: "opastuspiste",
        301: "laavu, kota tai kammi",
        302: "tupa",
        304: "ulkoilumaja/hiihtomaja",
        1110: "liikuntapuisto",
        1120: "lahiliikuntapaikka",
        1130: "ulkokuntoilupaikka",
        1140: "parkour-alue",
        1150: "skeitti-/rullaluistelupaikka",
        1160: "pyorailyalue",
        1170: "pyorailyrata/velodromi",
        1180: "frisbeegolfrata",
        1190: "pulkkamaki",
        1210: "yleisurheilun harjoitusalue",
        1220: "yleisurheilukentta",
        1310: "koripallokentta",
        1320: "lentopallokentta",
        1330: "beachvolley-/rantalentopallokentta",
        1340: "pallokentta",
        1350: "jalkapallostadion",
        1360: "pesapallokentta",
        1370: "tenniskentta",
        1380: "rullakiekkokentta",
        1390: "padelkentta",
        1395: "poytatennisalue",
        1510: "tekojaakentta/tekojaarata",
        1520: "luistelukentta",
        1530: "kaukalo",
        1540: "pikaluistelurata",
        1550: "luistelureitti",
        1560: "alamakiluistelurata",
        1610: "golfin harjoitusalue",
        1630: "golfin harjoitushalli",
        1640: "ratagolf",
        1650: "golfkentta",
        2110: "kuntokeskus",
        2120: "kuntosali",
        2130: "voimailusali",
        2140: "kamppailulajien sali",
        2150: "liikuntasali",
        2210: "liikuntahalli",
        2220: "monitoimihalli/areena",
        2225: "sisaleikki-/sisaaktiviteettipuisto",
        2230: "jalkapallohalli",
        2240: "salibandyhalli",
        2250: "skeittihalli",
        2260: "sulkapallohalli",
        2270: "squash-halli",
        2280: "tennishalli",
        2290: "petanque-halli",
        2295: "padelhalli",
        2310: "yksittainen yleisurheilun suorituspaikka",
        2320: "voimistelutila",
        2330: "poytatennistila",
        2340: "miekkailutila",
        2350: "tanssi-/ryhmaliikuntatila",
        2360: "sisaampumarata",
        2370: "sisakiipeilyseina",
        2380: "parkour-sali",
        2510: "harjoitusjaahalli",
        2520: "kilpajaahalli",
        2530: "pikaluisteluhalli",
        2610: "keilahalli",
        2620: "biljardisali",
        3110: "uimahalli",
        3120: "uima-allastila",
        3130: "kylpyla",
        3210: "maauimala/vesipuisto",
        3220: "uimaranta",
        3230: "uimapaikka",
        3240: "talviuintipaikka",
        3250: "vesiurheilukeskus",
        4110: "laskettelun suorituspaikka",
        4210: "curlingrata/-halli",
        4220: "hiihtotunneli",
        4230: "lumilautatunneli",
        4240: "lasketteluhalli",
        4320: "hyppyrimaki",
        4401: "kuntorata",
        4402: "hiihtolatu",
        4403: "kavelyreitti/ulkoilureitti",
        4404: "luontopolku",
        4405: "retkeilyreitti",
        4406: "monikayttoreitti",
        4407: "rullahiihtorata",
        4411: "maastopyorailyreitti",
        4412: "pyorailyreitti",
        4421: "moottorikelkkareitti",
        4422: "moottorikelkkaura",
        4430: "hevosreitti",
        4440: "koirahiihtolatu",
        4441: "koiravaljakkoreitti",
        4451: "melontareitti",
        4452: "vesiretkeilyreitti",
        4510: "suunnistusalue",
        4610: "ampumahiihdon harjoittelualue",
        4620: "ampumahiihtokeskus",
        4630: "maastohiihtokeskus",
        4640: "hiihtomaa",
        4710: "ulkokiipeilypaikka",
        4720: "kiipeilykallio",
        4810: "ampumarata",
        4820: "ampumaurheilukeskus",
        4830: "jousiammuntarata",
        4840: "jousiammuntamaastorata",
        5110: "soutustadion",
        5120: "purjehdusalue",
        5130: "moottoriveneurheilualue",
        5140: "vesihiihtoalue",
        5150: "melontakeskus",
        5160: "soudun ja melonnan sisaharjoittelutila",
        5210: "urheiluilmailualue",
        5310: "moottoriurheilukeskus",
        5320: "moottoripyorailyalue",
        5330: "moottorirata",
        5340: "karting-rata",
        5350: "kiihdytysrata",
        5360: "jokamies- ja rallicross-rata",
        5370: "speedway-/jaaspeedwayrata",
        6110: "ratsastuskentta",
        6120: "ratsastusmaneesi",
        6130: "esteratsastuskentta/-alue",
        6140: "ravirata",
        6150: "ovaalirata",
        6210: "koiraurheilualue",
        6220: "koiraurheiluhalli",
        7000: "huoltorakennus",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url=self._page_url(1), callback=self.parse_first_page, errback=self.parse_first_error)

    def parse_first_error(self, failure) -> None:
        request = failure.request
        raise CloseSpider(f"first page request failed: {request.url}")

    def _page_url(self, page: int) -> str:
        return (
            f"{self.api_base_url}/sports-sites?page={page}"
            f"&page-size={self.page_size}&statuses=active,out-of-service-temporarily"
        )

    def _stat(self, suffix: str, n: int = 1) -> None:
        stats = getattr(getattr(self, "crawler", None), "stats", None)
        if stats is not None:
            stats.inc_value(f"atp/{self.name}/{suffix}", n)

    def parse_first_page(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except (ValueError, AttributeError, TypeError) as exc:
            raise CloseSpider(f"bad JSON from {response.url}: {exc}") from exc
        if not isinstance(payload, dict):
            raise CloseSpider(f"expected JSON object from {response.url}")
        items = payload.get("items")
        if not isinstance(items, list) or not items:
            raise CloseSpider(f"first page returned no items: {response.url}")
        pagination = payload.get("pagination")
        if not isinstance(pagination, dict):
            raise CloseSpider(f"first page pagination not an object: {response.url}")
        total_pages = pagination.get("total-pages")
        if isinstance(total_pages, bool) or not isinstance(total_pages, int) or total_pages < 1:
            raise CloseSpider(f"unexpected pagination in {response.url}")
        yield from self.parse_page(response)
        for page in range(2, total_pages + 1):
            yield JsonRequest(url=self._page_url(page), callback=self.parse_page, errback=self.parse_page_error)

    def parse_page_error(self, failure) -> Iterable[JsonRequest] | None:
        request = failure.request
        if request.meta.get("retried"):
            self._stat("page/failed")
            self.logger.error("Page failed twice, dropping: %s", request.url)
            return
        self._stat("page/retried")
        self.logger.warning("Retrying failed page: %s", request.url)
        yield JsonRequest(
            url=request.url,
            callback=self.parse_page,
            errback=self.parse_page_error,
            meta={**request.meta, "retried": True},
        )

    def parse_page(self, response: TextResponse) -> Iterable[Feature]:
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except (ValueError, AttributeError, TypeError) as exc:
            self._stat("page/bad_json")
            self.logger.warning("Bad JSON page %s: %r", response.url, exc)
            return
        if not isinstance(payload, dict):
            self._stat("page/bad_envelope")
            self.logger.warning("Expected JSON object from %s", response.url)
            return
        items = payload.get("items") or []
        if not isinstance(items, list):
            self._stat("page/items_not_list")
            self.logger.warning("Expected items list from %s", response.url)
            return
        if not items:
            self._stat("page/empty")
            self.logger.warning("Empty items page: %s", response.url)
            return
        for site in items:
            try:
                if item := self._build_item(site):
                    yield item
            except (AttributeError, TypeError, ValueError, KeyError) as exc:
                # One misshapen record must not lose the other 99 on the page.
                self._stat("skipped/malformed_record")
                self.logger.warning("Skipping malformed record on %s: %r", response.url, exc)

    def _point(self, site: dict) -> tuple[float, float] | None:
        # Points pass through; polygon venues collapse to the mean of their
        # largest ring, which stays on large single-part venues and degrades
        # gracefully on scattered multi-part ones.
        try:
            features = ((site.get("location") or {}).get("geometries") or {}).get("features") or []
        except (AttributeError, TypeError):
            features = []
        if not isinstance(features, list):
            features = []
        best_lon, best_lat, best_n = 0.0, 0.0, 0
        points_only = True
        for gtype, coords in self._iter_geometries(features):
            try:
                if gtype == "Point" and len(coords) >= 2:
                    return float(coords[0]), float(coords[1])
                if gtype == "MultiPoint":
                    if (first := self._first_point(coords)) is not None:
                        return first
                if gtype in ("LineString", "MultiLineString"):
                    # Anomalous on a mapped type: excluded route codes never
                    # reach _point (they return as excluded/ above).
                    self._stat("geometry/linear")
                    continue
                if gtype in ("Polygon", "MultiPolygon"):
                    points_only = False
                    if not coords:
                        continue
                    rings = [coords[0]] if gtype == "Polygon" else [poly[0] for poly in coords if poly]
                    rlon, rlat, rn = self._best_ring(rings)
                    if rn > best_n:
                        best_lon, best_lat, best_n = rlon, rlat, rn
            except (AttributeError, TypeError, ValueError, KeyError):
                # One malformed coordinate must not lose the other 99 records.
                self._stat("geometry/malformed_coord")
                continue
        if best_n:
            self._stat("geometry/polygon_centroid")
            return best_lon / best_n, best_lat / best_n
        if not points_only:
            self._stat("geometry/polygon_empty")
        return None

    def _iter_geometries(self, features: object) -> Iterable[tuple[str | None, list]]:
        # Yields (type, coordinates) pairs, expanding GeometryCollections;
        # unknown types are counted and skipped, and non-sequence coordinates
        # can never be valid positions.
        if not isinstance(features, list):
            return
        for feature in features:
            geometry = (feature.get("geometry") if isinstance(feature, dict) else None) or {}
            if not isinstance(geometry, dict):
                continue
            if geometry.get("type") == "GeometryCollection":
                yield from self._iter_geometries([{"geometry": sub} for sub in geometry.get("geometries") or []])
                continue
            gtype = geometry.get("type")
            if gtype not in self.KNOWN_GEOMETRIES:
                self._stat("geometry/unknown_type")
                continue
            coords = geometry.get("coordinates")
            yield gtype, coords if isinstance(coords, (list, tuple)) else []

    @staticmethod
    def _first_point(coords: object) -> tuple[float, float] | None:
        # First finite position; bad vertices are skipped individually.
        if not isinstance(coords, (list, tuple)):
            return None
        for point in coords:
            try:
                if len(point) >= 2:
                    lon, lat = float(point[0]), float(point[1])
                    if math.isfinite(lon) and math.isfinite(lat):
                        return lon, lat
            except (AttributeError, TypeError, ValueError, KeyError):
                continue
        return None

    @staticmethod
    def _best_ring(rings: object) -> tuple[float, float, int]:
        # Mean of the vertex-richest ring; scattered multi-part venues land
        # on their largest part instead of in the gaps between parts.
        best = (0.0, 0.0, 0)
        if not isinstance(rings, list):
            return best
        for ring in rings:
            rlon, rlat, rn = LipasFISpider._accumulate(ring)
            if rn > best[2]:
                best = (rlon, rlat, rn)
        return best

    @staticmethod
    def _accumulate(ring: object) -> tuple[float, float, int]:
        # Vertex-mean of one exterior ring; bad vertices are skipped
        # individually and the duplicated closing vertex is not double-counted.
        lon_sum, lat_sum, n = 0.0, 0.0, 0
        if not isinstance(ring, list):
            return lon_sum, lat_sum, n
        if len(ring) > 1 and ring[0] == ring[-1]:
            ring = ring[:-1]
        for point in ring:
            try:
                if len(point) >= 2:
                    lon_sum += float(point[0])
                    lat_sum += float(point[1])
                    n += 1
            except (AttributeError, TypeError, ValueError, KeyError):
                continue
        return lon_sum, lat_sum, n

    @staticmethod
    def _type_mapping(site: dict) -> tuple[object, tuple | str | None]:
        kind = site.get("type")
        raw = kind.get("type-code") if isinstance(kind, dict) else None
        # Bools and non-integral or non-finite floats are never codes; reject
        # them rather than truncate (1520.5 must not resolve to 1520).
        if isinstance(raw, bool) or (isinstance(raw, float) and not (math.isfinite(raw) and raw.is_integer())):
            raw = None
        try:
            # Numeric strings from upstream still resolve to the right row.
            type_code: object = int(raw)
        except (TypeError, ValueError, OverflowError):
            # Containers can never be codes (and are unhashable for the
            # lookup); anything else falls back to generic, never drop.
            type_code = None if not isinstance(raw, (str, int, float)) else raw
        return type_code, LipasFISpider.TYPE_MAP.get(type_code, "unknown")

    @staticmethod
    def _ref(lipas_id: object) -> str | None:
        # National ids are positive ints; whole floats still resolve, while
        # bools, containers, non-finite numbers and blank/zero strings are
        # never valid refs.
        if isinstance(lipas_id, bool):
            return None
        if isinstance(lipas_id, float):
            if not math.isfinite(lipas_id):
                return None
            if lipas_id.is_integer():
                lipas_id = int(lipas_id)
        elif isinstance(lipas_id, str):
            lipas_id = lipas_id.strip()
        if isinstance(lipas_id, (int, str)) and str(lipas_id) not in {"", "0", "0.0"}:
            return str(lipas_id)
        return None

    def _build_item(self, site: dict) -> Feature | None:
        ref = self._ref(site.get("lipas-id"))
        if ref is None:
            self._stat("skipped/no_ref")
            return None
        lipas_id = ref
        type_code, mapping = self._type_mapping(site)
        if mapping is None:
            self._stat(f"excluded/{type_code}")
            return None
        if mapping == "unknown":
            self._stat(f"unmapped/{type_code}")
            self.logger.debug("Unknown LIPAS type-code %r on %r", type_code, lipas_id)
        # Belt and braces: the query filter should only return these two.
        if str(site.get("status") or "active").strip().lower() not in ("active", "out-of-service-temporarily"):
            self._stat("skipped/status")
            return None
        name = self._text(site.get("name")).strip(" /")
        if not name or self._is_placeholder(name):
            self._stat("skipped/no_name")
            return None
        location = site.get("location") or {}
        if not isinstance(location, dict):
            location = {}
        address = self._text(location.get("address"))
        if self._is_placeholder(address):
            address = ""
        point = self._point(site)
        if point is not None and not (math.isfinite(point[0]) and math.isfinite(point[1])):
            self._stat("coords/non_finite")
            point = None
        if point is None and not address:
            self._stat("skipped/neither_address_nor_coords")
            return None
        item = Feature()
        item["ref"] = ref
        item["country"] = "FI"
        self._apply_name(item, type_code, name)
        if point is not None:
            item["lon"], item["lat"] = point
        else:
            self._stat("coords/missing_but_address_kept")
            self.logger.debug("No usable geometry on %r", lipas_id)
        # Bare street names without numbers stay the full freeform line.
        if address:
            item["street_address"] = address
        if postcode := self._text(location.get("postal-code")):
            if self._is_placeholder(postcode):
                self._stat("empty/postcode_placeholder")
            elif postcode.replace("0", "").strip():
                item["postcode"] = postcode
            else:
                self._stat("empty/postcode_zeros")
        # V2 post towns are the FI addr:city equivalent (we use only the
        # post-office field); upstream municipality disambiguators cut.
        if (post_office := self._text(location.get("postal-office"))) and not self._is_placeholder(post_office):
            item["city"] = post_office.split("(", 1)[0].strip() or post_office
        else:
            self._stat("empty/post_office")
        self._apply_category(item, mapping)
        self._apply_brand(item, type_code)
        self._apply_contact(item, site)
        return item

    @staticmethod
    def _fold(value: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).casefold()

    # Heads naming institutions host the facility (schools, churches,
    # service centres); matching is end-anchored with trailing parentheticals
    # stripped ("Laajasalon peruskoulu (ylaaste)" still matches).
    INSTITUTION_HEADS = ("koulu", "lukio", "opisto", "paivakoti", "skola", "kirkko", "palvelukeskus")

    def _is_institution_head(self, head: str) -> bool:
        base = head.strip()
        if base.endswith(")"):
            base = base.rsplit("(", 1)[0].strip()
        folded = self._fold(base)
        return any(folded.endswith(word) for word in self.INSTITUTION_HEADS)

    def _is_type_name(self, base: str, type_code: object) -> bool:
        # Tail restating the record's own type (comma/"tai" alternatives
        # split: "laavu" matches 301 "laavu, kota tai kammi"); compounds
        # match end-anchored ("jaakiekkokaukalo" on a kaukalo record).
        typename = self.TYPE_FI.get(type_code)
        if not isinstance(typename, str):
            return False
        alts = {typename}
        for part in typename.replace(" tai ", ",").split(","):
            if part := part.strip():
                alts.add(part)
        folded = self._fold(base)
        return any(folded == alt or folded.endswith(alt) for alt in alts)

    def _apply_name(self, item: Feature, type_code: object, raw_name: str) -> None:
        # "EBK-Honka Areena / Jalkapallohalli": the tail restates this
        # record's own type, so the head is the name. A numbered tail names
        # a distinct facility inside the venue ("...puisto / Luistelukentta
        # 1"), and institution heads always host ("Munkkivuoren ala-asteen
        # koulu / Liikuntasali"): facility-in-venue, full signed form kept
        # in official_name. Only the last " / " splits, so multi-slash heads
        # keep their remainder ("A / B / tyyppi" names "A / B").
        if " / " not in raw_name:
            item["name"] = raw_name
            return
        head, _, tail = raw_name.rpartition(" / ")
        head, tail = head.strip(), tail.strip()
        if not head or not tail:
            # Degenerate signing ("A / ", " / "): the surviving side is the
            # name, and a fully empty name drops as no_name downstream.
            self._stat("name/slash_kept")
            item["name"] = head or tail
            return
        if self._is_institution_head(head):
            item["name"] = tail
            item["located_in"] = head
            item["extras"]["official_name"] = raw_name
            self._stat("name/slash_facility")
            return
        words = tail.split()
        numbered = len(words) > 1 and words[-1].isdigit()
        base = " ".join(words[:-1]) if numbered else tail
        if self._is_type_name(base, type_code):
            item["extras"]["official_name"] = raw_name
            if numbered:
                item["name"] = tail
                item["located_in"] = head
            else:
                item["name"] = head
            self._stat("name/split_slash")
            return
        self._stat("name/slash_kept")
        item["name"] = raw_name

    def _apply_category(self, item: Feature, mapping: tuple | str) -> None:
        if mapping == "unknown":
            apply_category(Categories.GENERIC_POI, item)
            return
        category, sport = mapping
        apply_category(category, item)
        if sport is not None:
            add_sport(sport, item)

    # Name-anchored gym chains with a Wikidata brand item. Exact anchors only:
    # anything else brands nothing, never a guess. Fressi and Elixia have LIPAS
    # volume but no brand item yet, so they stay unbranded pending their NSI PRs.
    # "gogo express" is deliberately left out: those venues belong to the separate
    # GoGo Express Oy (gogoexpress.fi), whose item Q120884765 is a place, not a
    # brand, so it must not inherit the GOGO brand.
    BRANDS = (
        ("kuntokeskus liikku", "Kuntokeskus Liikku", "Q28721474"),
        ("liikku", "Kuntokeskus Liikku", "Q28721474"),  # short form "Liikku X"
        ("fitness24seven", "Fitness24Seven", "Q61112447"),
        ("fitness 24/7", "Fitness24Seven", "Q61112447"),  # spaced "Fitness 24/7 X"
        ("easyfit", "EasyFit", "Q141740469"),
        ("ladyline", "LadyLine", "Q141740470"),
        ("forever", "Forever", "Q141740471"),
        ("gogo", "GOGO Liikuntakeskus", "Q141740472"),  # "gogo express" excluded above
    )
    # Anchors whose venues belong to a different operator and must not take the
    # BRANDS entry they would otherwise prefix-match.
    NO_BRAND = ("gogo express",)
    GYM_TYPES = frozenset({2110, 2120, 2130})

    def _apply_brand(self, item: Feature, type_code: object) -> None:
        # Brand from the (post-split) name head; branch suffix stays in
        # name ("Kuntokeskus Liikku Hermia" keeps its branch).
        if type_code not in self.GYM_TYPES:
            return
        folded = " ".join(self._fold(item.get("name") or "").split())
        for stem in self.NO_BRAND:
            if folded == stem or folded.startswith(stem + " "):
                self._stat(f"brand/none/{stem.replace(' ', '_')}")
                return
        for stem, brand, qid in self.BRANDS:
            if folded == stem or folded.startswith(stem + " "):
                item["brand"] = brand
                item["brand_wikidata"] = qid
                self._stat(f"brand/{stem.replace(' ', '_').replace('/', '_')}")
                return

    def _apply_contact(self, item: Feature, site: dict) -> None:
        if website := self._normalize_website(site.get("www")):
            item["website"] = website
        if phone := self._text(site.get("phone-number")):
            item["phone"] = phone
        else:
            self._stat("empty/phone")
        if email := self._text(site.get("email")):
            item["email"] = email
        else:
            self._stat("empty/email")

    @staticmethod
    def _text(value: object) -> str:
        # Plain strings pass through with format characters dropped and
        # internal whitespace collapsed; whole floats and nonzero finite ints
        # stringify (API types these fields as strings, so numbers are
        # upstream quirks); bools, containers and NaN/inf/zero are never valid.
        if isinstance(value, str):
            value = "".join(c for c in value if unicodedata.category(c) != "Cf")
            return " ".join(value.split())
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return ""
        if not math.isfinite(value) or value == 0:
            return ""
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        return str(value)

    @staticmethod
    def _is_placeholder(value: str) -> bool:
        return value.casefold() in {"0", "0.0", "n/a", "-", "–", "—", "?", "null"}

    @staticmethod
    def _repair_scheme(website: str) -> str:
        # Repair upstream scheme typos: missing slashes ("https:/x"), doubled or
        # transposed letters ("hhttps://x", "hpps://x") and unrelated schemes
        # ("ps://x"). The host and path survive; a bare scheme is never emitted.
        if "://" not in website:
            website = re.sub(r"^(https?:)/(?!/)", r"\1//", website)
            if "://" not in website:
                return "https://" + website.lstrip("/")
        scheme, _, rest = website.partition("://")
        if scheme.lower() not in ("http", "https"):
            return "https://" + rest.lstrip("/")
        return website

    @staticmethod
    def _is_valid_host(hostname: str | None) -> bool:
        # Mirrors the ATP check_item_properties hostname rule so a normalised URL
        # is never rejected (and logged as an ERROR) downstream.
        if not hostname or len(hostname) > 253:
            return False
        for part in hostname.split("."):
            if not part or len(part) > 63 or part.startswith("-") or part.endswith("-"):
                return False
            if part.lower().startswith("xn--"):
                return False
            for ch in part:
                category = unicodedata.category(ch)
                if not (category.startswith("L") or category == "Nd" or ch == "-"):
                    return False
        return True

    def _normalize_website(self, raw: object | None) -> str | None:
        if not isinstance(raw, str) or not (website := raw.strip()):
            return None
        # Drop format/zero-width marks and leading junk seen upstream
        # (":www.x", "-https://x").
        website = "".join(c for c in website if unicodedata.category(c) != "Cf").strip().lstrip(" :-")
        if not website or self._is_placeholder(website) or " " in website:
            return None
        website = self._repair_scheme(website)
        try:
            parsed = urlparse(website)
        except ValueError:
            self._stat("website/invalid")
            return None
        if not parsed.netloc:
            self._stat("website/invalid")
            return None
        if "," in parsed.netloc:
            # Upstream comma-for-dot typos in the host ("www.tornio,fi").
            website = urlunparse(parsed._replace(netloc=parsed.netloc.replace(",", ".")))
            parsed = urlparse(website)
        if not self._is_valid_host(parsed.hostname):
            # Emitting these would only make the ATP pipeline log an ERROR.
            self._stat("website/invalid")
            return None
        return website
