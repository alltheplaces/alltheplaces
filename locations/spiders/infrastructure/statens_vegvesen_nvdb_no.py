import csv
import re
from typing import AsyncIterator, Iterable

import scrapy
from scrapy import Request
from scrapy.http import Response

from locations.categories import MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature
from locations.licenses import Licenses

# NVDB vegobjekttype ID -> OSM category mapping. (https://datakatalogen.atlas.vegvesen.no/)
# Each entry: {type_id: (label, category_dict, name_attr_key_or_None)}
# name_attr_key is the egenskaper "navn" value used to extract a name for the Feature.
OBJECT_TYPE_MAP = {
    22: ("Ferist", {"barrier": "cattle_grid"}, None),
    23: ("Vegbom", {"barrier": "gate"}, None),
    25: ("Leskur", {"amenity": "shelter", "shelter_type": "public_transport"}, None),
    29: ("Strøsandkasse", {"amenity": "grit_bin"}, None),
    37: ("Vegkryss", {"highway": "motorway_junction"}, "Navn"),
    39: ("Rasteplass", {"highway": "rest_area"}, "Navn"),
    40: ("Snuplass", {"highway": "turning_circle"}, None),
    45: ("Bomstasjon", {"barrier": "toll_booth"}, "Navn bomstasjon"),
    47: ("Trafikklomme", {"highway": "passing_place"}, None),
    60: ("Bru", {"man_made": "bridge"}, "Navn"),
    64: ("Ferjekai", {"amenity": "ferry_terminal"}, "Navn"),
    66: ("Skredoverbygg", {"tunnel": "avalanche_protector"}, "Navn"),
    67: ("Tunnelløp", {"tunnel": "yes", "man_made": "tunnel"}, "Navn"),
    83: ("Kum", {"man_made": "manhole"}, None),
    87: ("Belysningspunkt", {"highway": "street_lamp", "support": "pole"}, None),
    89: ("Signalanlegg", {"highway": "traffic_signals"}, "Navn"),
    96: ("Skiltplate", {"highway": "traffic_sign"}, None),
    100: ("Jernbanekryssing", {"railway": "level_crossing"}, None),
    103: ("Fartsdemper", {"traffic_calming": "bump"}, None),
    153: ("Værstasjon", {"man_made": "monitoring_station"}, None),
    162: ("ATK-punkt", {"man_made": "surveillance", "surveillance:type": "camera", "enforcement": "maxspeed"}, None),
    163: ("Kamera", {"man_made": "surveillance", "surveillance:type": "camera"}, None),
    174: ("Gangfelt", {"highway": "crossing"}, None),
    180: ("Nødtelefon", {"emergency": "phone"}, None),
    199: ("Trær", {"natural": "tree"}, None),
    209: ("Hydrant", {"emergency": "fire_hydrant"}, None),
    213: ("Brannslokningsapparat", {"emergency": "fire_extinguisher"}, None),
    243: ("Toalettanlegg", {"amenity": "toilets"}, None),
    451: ("Sykkelparkering", {"amenity": "bicycle_parking"}, None),
    470: ("Antenne", {"man_made": "antenna"}, None),
    607: ("Vegsperring", {"barrier": "yes"}, None),
    809: ("Døgnhvileplass", {"highway": "rest_area", "hgv": "yes"}, "Navn"),
    854: ("Kuldeport", {"barrier": "roller_shutter"}, None),
    875: ("Trapp", {"highway": "steps"}, None),
    996: ("Flaggstang", {"man_made": "flagpole"}, None),
}

# Regex to parse WKT POINT geometries: "POINT (x y)" or "POINT Z(x y z)"
WKT_POINT_RE = re.compile(r"POINT\s*Z?\s*\(\s*([-\d.]+)\s+([-\d.]+)")
# Regex to extract parenthesised coordinate lists from WKT
_WKT_COORD_LIST_RE = re.compile(r"\(\s*([^()]+?)\s*\)")


def _parse_wkt_coords(coord_str: str) -> list[list[float]]:
    """Parse a comma-separated WKT coordinate string to GeoJSON coordinates.

    Swaps EPSG:4326 (lat, lon) axis order to GeoJSON [lon, lat].
    Drops the Z coordinate if present.
    """
    coords: list[list[float]] = []
    for pair in coord_str.split(","):
        parts = pair.strip().split()
        if len(parts) >= 2:
            try:
                lat = float(parts[0])
                lon = float(parts[1])
                coords.append([lon, lat])
            except ValueError:
                continue
    return coords


def _wkt_to_geojson(wkt: str) -> dict | None:
    """Convert a WKT geometry string to a GeoJSON geometry dict.

    NVDB export with srid=4326 returns coordinates in EPSG:4326
    axis order (latitude, longitude), which are swapped to GeoJSON
    [longitude, latitude] order per RFC 7946.

    Supported types: POINT, LINESTRING, MULTILINESTRING (with optional Z).
    """
    if not wkt:
        return None
    wkt = wkt.strip()

    if wkt.startswith("POINT"):
        m = WKT_POINT_RE.search(wkt)
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            return {"type": "Point", "coordinates": [lon, lat]}
        return None

    if wkt.startswith("LINESTRING"):
        ring_match = _WKT_COORD_LIST_RE.search(wkt)
        if not ring_match:
            return None
        coords = _parse_wkt_coords(ring_match.group(1))
        if len(coords) >= 2:
            return {"type": "LineString", "coordinates": coords}
        return None

    if wkt.startswith("MULTILINESTRING"):
        lines: list[list[list[float]]] = []
        for ring_match in _WKT_COORD_LIST_RE.finditer(wkt):
            coords = _parse_wkt_coords(ring_match.group(1))
            if len(coords) >= 2:
                lines.append(coords)
        if len(lines) == 1:
            return {"type": "LineString", "coordinates": lines[0]}
        if lines:
            return {"type": "MultiLineString", "coordinates": lines}
        return None

    return None


# Regex to extract property name from CSV column header: "EGS.<NAME>.<ID>"
_EGS_COL_RE = re.compile(r"^EGS\.(.+)\.(\d+)$")
# Regex to strip unit annotations like (M), (STK), (KR), (M2)
_UNIT_SUFFIX_RE = re.compile(r"\s*\([^)]*\)\s*$")
# Regex to detect numeric values with comma decimal separator
_COMMA_DECIMAL_RE = re.compile(r"^-?\d+,\d+$")


def _normalize_egs_column(header: str) -> str | None:
    """Normalize a CSV EGS column header to a property name matching NVDB conventions.

    Examples:
        "EGS.LENGDE (M).1317" -> "Lengde"
        "EGS.NAVN BOMSTASJON.1078" -> "Navn bomstasjon"
        "EGS.TYPE.1156" -> "Type"
        "EGS.NSR_STOPPLACE_ID.10727" -> "Nsr_stopplace_id"
    """
    m = _EGS_COL_RE.match(header)
    if not m:
        return None
    name = m.group(1)
    # Strip unit annotations in parentheses at end of name
    name = _UNIT_SUFFIX_RE.sub("", name)
    # Capitalize: first character upper, rest lower (matches NVDB JSON property naming)
    return name.capitalize() if name else None


def _normalize_csv_value(val: str) -> str:
    """Replace Norwegian comma decimal separator with dot in numeric values."""
    if _COMMA_DECIMAL_RE.match(val):
        return val.replace(",", ".")
    return val


class StatensVegvesenNvdbNOSpider(scrapy.Spider):
    """
    Spider for the Norwegian National Road Database (NVDB) CSV export service,
    operated by Statens vegvesen (Norwegian Public Roads Administration).

    Extracts road infrastructure objects from NVDB and maps them to
    OpenStreetMap-compatible categories including toll booths, bridges,
    tunnels, weather stations, traffic signals, rest areas, pedestrian
    crossings, fire hydrants, trees, and more.

    Export API documentation: https://www.nvdb.no/hent-og-se-data/eksport/nvdb-eksport/brukerveiledning/
    """

    name = "statens_vegvesen_nvdb_no"
    allowed_domains = ["nvdb-eksport.atlas.vegvesen.no"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 600}
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Statens vegvesen"
    }

    async def start(self) -> AsyncIterator[Request]:
        for type_id in OBJECT_TYPE_MAP:
            yield Request(
                url=f"https://nvdb-eksport.atlas.vegvesen.no/vegobjekter/{type_id}.csv?inkluder=alle&srid=4326",
                headers={"X-Client": "alltheplaces", "Accept": "text/csv"},
                cb_kwargs={"type_id": type_id},
            )

    def parse(self, response: Response, type_id: int) -> Iterable[Feature]:
        label, category, name_attr = OBJECT_TYPE_MAP[type_id]

        reader = csv.reader(response.text.splitlines(), delimiter=";")
        headers = next(reader, None)
        if not headers:
            return

        # Build column index maps
        col_map: dict[str, int] = {}
        egs_map: dict[int, str] = {}
        for i, h in enumerate(headers):
            col_map[h] = i
            if h.startswith("EGS."):
                name = _normalize_egs_column(h)
                if name:
                    egs_map[i] = name

        obj_id_idx = col_map.get("OBJ.VEGOBJEKT-ID")
        geo_idx = col_map.get("GEO.GEOMETRI")

        if obj_id_idx is None or geo_idx is None:
            return

        for row in reader:
            if len(row) <= max(obj_id_idx, geo_idx):
                continue

            obj_id = row[obj_id_idx].strip()
            if not obj_id:
                continue

            # Parse geometry from GEO.GEOMETRI column (EPSG:4326 WKT)
            wkt = row[geo_idx].strip()
            geojson = _wkt_to_geojson(wkt)
            if not geojson:
                continue

            # Build property dict from EGS columns
            props: dict[str, str] = {}
            for idx, name in egs_map.items():
                if idx < len(row):
                    val = row[idx].strip()
                    if val and not val.startswith(("POINT", "LINESTRING", "POLYGON")):
                        props[name] = _normalize_csv_value(val)

            item = Feature()
            item["ref"] = f"NVDB:{type_id}:{obj_id}"
            if geojson["type"] == "Point":
                item["lat"] = geojson["coordinates"][1]
                item["lon"] = geojson["coordinates"][0]
            else:
                item["geometry"] = geojson

            # Extract name
            if name_attr:
                name = props.get(name_attr)
                if name:
                    item["name"] = name

            # Apply OSM category tags
            apply_category(category, item)

            # Apply common property mappings
            self._apply_common_props(item, props)

            # Apply type-specific extras
            if not self._apply_type_extras(item, type_id, props):
                continue

            yield item

    def _apply_common_props(self, item: Feature, props: dict) -> None:
        """Apply common NVDB property mappings shared across many object types.

        Maps standard NVDB properties to OSM-compatible tags:
        - Tilleggsinformasjon -> description
        - Etableringsår -> start_date
        - Produsent -> manufacturer
        - Produktnavn -> model
        """
        if description := props.get("Tilleggsinformasjon"):
            item["extras"]["description"] = description
        if start_date := props.get("Etableringsår"):
            item["extras"]["start_date"] = start_date
        if manufacturer := props.get("Produsent"):
            item["extras"]["manufacturer"] = manufacturer
        if model := props.get("Produktnavn"):
            item["extras"]["model"] = model
        if operator := props.get("Vedlikeholdsansvarlig"):
            item["operator"] = operator

    def _apply_material(self, item: Feature, props: dict) -> None:
        """Map NVDB Materialtype to OSM material tag."""
        if material_type := props.get("Materialtype"):
            if material_type in self._MATERIAL_TYPE_MAP:
                item["extras"]["material"] = self._MATERIAL_TYPE_MAP[material_type]
            else:
                item["extras"]["material"] = material_type.lower()

    def _apply_type_extras(self, item: Feature, type_id: int, props: dict) -> bool:
        """Apply type-specific OSM tags based on the object type and its properties.
        Returns True if the item should be kept, False to skip it.
        """
        handler = {
            22: self._extras_ferist,
            23: self._extras_vegbom,
            25: self._extras_leskur,
            29: self._extras_strosandkasse,
            37: self._extras_motorvegkryss,
            39: self._extras_rasteplass,
            40: self._extras_snuplass,
            45: self._extras_bomstasjon,
            47: self._extras_moteplass,
            60: self._extras_bru,
            64: self._extras_ferjekai,
            66: self._extras_skredsikring,
            67: self._extras_tunnellop,
            89: self._extras_signalanlegg,
            96: self._extras_skiltplate,
            100: self._extras_jernbanekryssing,
            103: self._extras_fartsdemper,
            153: self._extras_vaerstasjon,
            163: self._extras_kamera,
            174: self._extras_gangfelt,
            180: self._extras_nodtelefon,
            199: self._extras_traer,
            209: self._extras_hydrant,
            213: self._extras_brannslokningsapparat,
            243: self._extras_toalettanlegg,
            451: self._extras_sykkelparkering,
            470: self._extras_antenne,
            607: self._extras_sperring,
            809: self._extras_dognhvileplass,
            854: self._extras_kuldeport,
            875: self._extras_trapp,
            996: self._extras_flaggstang,
        }.get(type_id)
        if handler is None:
            return True
        return handler(item, props)

    def _extras_ferist(self, item: Feature, props: dict) -> bool:
        """Type 22: Ferist (Cattle grid)."""
        if cattle_grid_type := props.get("Type"):
            if cattle_grid_type == "Elektrisk":
                item["extras"]["cattle_grid"] = "electric"
        return True

    _BARRIER_TYPE_MAP = {
        "Heve-/senkebom": "lift_gate",
        "Svingbom": "swing_gate",
        "Stolpe/pullert/kjegle": "bollard",
        "Rørgelender": "cycle_barrier",
        "Steinblokk": "block",
        "Betongblokk": "jersey_barrier",
        "Bussluse": "bus_trap",
        "Annen type vegbom/sperring": "gate",
        "Låst bom": "yes",
    }

    _MATERIAL_TYPE_MAP = {
        # Type 23 (Vegbom) materials
        "Stål": "steel",
        "Aluminium": "aluminium",
        "Tre": "wood",
        "Plast": "plastic",
        "Betong": "concrete",
        "Stein": "stone",
        # Type 25 (Leskur) materials
        "Metall, aluminium": "aluminium",
        "Metall, stål, galvanisert": "steel",
        "Metall": "metal",
        "Pleksiglass": "plexiglass",
        "Polykarbonat": "polycarbonate",
        "Herdet glass": "tempered_glass",
        "Glassfiber": "fiberglass",
        # Type 875 (Trapp) materials
        "Granitt": "granite",
    }

    def _extras_vegbom(self, item: Feature, props: dict) -> bool:
        """Type 23: Vegbom (Road barrier)."""
        self._apply_material(item, props)
        bom_type = props.get("Type", "")
        if bom_type in self._BARRIER_TYPE_MAP:
            item["extras"]["barrier"] = self._BARRIER_TYPE_MAP[bom_type]
        bruk = props.get("Bruksområde", "")
        if bruk == "Gang-/sykkelveg, sluse" and (bom_type == "Annen type vegbom/sperring" or not bom_type):
            item["extras"]["barrier"] = "swing_gate"
        if bruk == "Høyfjellsovergang":
            item["extras"]["access"] = "yes"
            if stedsnavn := props.get("Stedsnavn"):
                item["name"] = stedsnavn
        if bruk in ("Tunnel", "Bomstasjon", "Ferjekai", "Jernbane"):
            return False
        return True

    def _extras_strosandkasse(self, item: Feature, props: dict) -> bool:
        """Type 29: Strøsandkasse (Grit bin)."""
        if volume := props.get("Volum"):
            item["extras"]["capacity"] = f"{volume} l"
        return True

    _TOILET_DISPOSAL_MAP = {
        "Vannklosett": "flush",
        "Tørrklosett": "dry_toilet",
    }

    def _extras_toalettanlegg(self, item: Feature, props: dict) -> bool:
        """Type 243: Toalettanlegg (Toilets)."""
        if toilet_type := props.get("Type"):
            if disposal := self._TOILET_DISPOSAL_MAP.get(toilet_type):
                item["extras"]["toilets:disposal"] = disposal
        if num_toilets := props.get("Antall klosett"):
            item["extras"]["toilets:number"] = num_toilets
        if props.get("Universelt utformet") == "Ja":
            item["extras"]["wheelchair"] = "yes"
        elif props.get("Universelt utformet") == "Nei":
            item["extras"]["wheelchair"] = "no"
        return True

    def _extras_sykkelparkering(self, item: Feature, props: dict) -> bool:
        """Type 451: Sykkelparkering (Bicycle parking)."""
        if props.get("Sykkelstativ") == "Ja":
            item["extras"]["bicycle_parking"] = "stands"
        if props.get("Takoverbygg") == "Ja":
            item["extras"]["covered"] = "yes"
        elif props.get("Takoverbygg") == "Nei":
            item["extras"]["covered"] = "no"
        if capacity := props.get("Antall sykler totalt"):
            item["extras"]["capacity"] = capacity
        return True

    def _extras_leskur(self, item: Feature, props: dict) -> bool:
        """Type 25: Leskur (Public transport shelter)."""
        self._apply_material(item, props)
        if props.get("Innvendig belysning") == "Ja":
            item["extras"]["lit"] = "yes"
        if props.get("Sittemulighet") == "Ja":
            item["extras"]["bench"] = "yes"
        if props.get("Areal tilpasset rullestol") == "Ja":
            item["extras"]["wheelchair"] = "yes"
        return True

    def _extras_motorvegkryss(self, item: Feature, props: dict) -> bool:
        """Type 37: Vegkryss (Road junction — filtered to motorway junctions only)."""
        if "Planskilt kryss" not in props.get("Type", ""):
            return False
        if ref := props.get("Kryssnummer"):
            item["extras"]["ref"] = str(ref)
        return True

    def _extras_rasteplass(self, item: Feature, props: dict) -> bool:
        """Type 39: Rasteplass (Rest area)."""
        if cap_small := props.get("Antall oppstillingspl. små kjt."):
            item["extras"]["capacity:car"] = cap_small
        if cap_large := props.get("Antall oppstillingspl. store kjt."):
            item["extras"]["capacity:hgv"] = cap_large
        if props.get("Fast dekke") == "Ja":
            item["extras"]["surface"] = "paved"
        return True

    def _extras_snuplass(self, item: Feature, props: dict) -> bool:
        """Type 40: Snuplass (Turning point)."""
        if "trafikkøy" in props.get("Utforming", "").lower():
            item["extras"]["highway"] = "turning_loop"
        return True

    def _extras_bomstasjon(self, item: Feature, props: dict) -> bool:
        """Type 45: Bomstasjon (Toll booth)."""
        if operator_name := props.get("Navn bompengeanlegg"):
            item["extras"]["toll:operator"] = operator_name
        if url := props.get("Link til bomstasjon"):
            if not url.startswith("http"):
                url = "https://" + url
            item["website"] = url
        if bom_type := props.get("Bomstasjonstype"):
            if "AutoPASS" in bom_type:
                item["extras"]["payment:autopass"] = "yes"
            if "automatisk" in bom_type.lower():
                item["extras"]["toll:automatic"] = "yes"
        return True

    def _extras_moteplass(self, _item: Feature, props: dict) -> bool:
        """Type 47: Trafikklomme (Traffic bay — filtered to passing places only)."""
        return props.get("Bruksområde", "") == "Møteplass"

    _BRIDGE_MOVABLE_MAP = {
        "klaffebru": "bascule",
        "svingbru": "swing",
        "rullebru": "retractable",
    }

    def _extras_bru(self, item: Feature, props: dict) -> bool:
        """Type 60: Bru (Bridge)."""
        if length := props.get("Lengde"):
            item["extras"]["length"] = f"{length} m"
        if year := props.get("Byggeår"):
            item["extras"]["start_date"] = year
        if name := item.get("name"):
            item["extras"]["bridge:description"] = name.replace("  ", " ").replace(" Bru", " bru").strip()
        if bygge_type := props.get("Byggverkstype"):
            self._apply_bridge_structure(item, bygge_type.lower())
        return True

    def _apply_bridge_structure(self, item: Feature, bridge_type: str) -> None:
        """Map Norwegian bridge construction type to OSM bridge:structure."""
        if "hengebru" in bridge_type:
            item["extras"]["bridge:structure"] = "suspension"
        elif "bue" in bridge_type or "hvelv" in bridge_type:
            item["extras"]["bridge:structure"] = "arch"
        elif "fagverk" in bridge_type:
            item["extras"]["bridge:structure"] = "truss"
        elif bridge_type in self._BRIDGE_MOVABLE_MAP:
            item["extras"]["bridge"] = "movable"
            item["extras"]["bridge:movable"] = self._BRIDGE_MOVABLE_MAP[bridge_type]
        elif bridge_type == "flytebru":
            item["extras"]["bridge:structure"] = "floating"
        else:
            item["extras"]["bridge:structure"] = bridge_type

    def _extras_ferjekai(self, item: Feature, props: dict) -> bool:
        """Type 64: Ferjekai (Ferry terminal)."""
        if name := item.get("name"):
            item["name"] = name.replace("Fk", "").replace("Kai", "").replace("  ", " ").strip()
        if nsr_id := props.get("Nsr_stopplace_id"):
            item["extras"]["ref:nsrq"] = nsr_id
        return True

    def _extras_skredsikring(self, item: Feature, _props: dict) -> bool:
        """Type 66: Skredoverbygg (Avalanche protector)."""
        item["extras"]["layer"] = "-1"
        return True

    def _extras_tunnellop(self, item: Feature, props: dict) -> bool:
        """Type 67: Tunnelløp (Tunnel)."""
        if length := props.get("Lengde"):
            item["extras"]["tunnel:length"] = f"{length} m"
        if width := props.get("Bredde"):
            item["extras"]["width"] = f"{width} m"
        if height := props.get("Høyde"):
            item["extras"]["maxheight"] = height
        if year := props.get("Åpningsår"):
            item["extras"]["start_date"] = year
        return True

    def _extras_signalanlegg(self, item: Feature, props: dict) -> bool:
        """Type 89: Signalanlegg (Traffic signals)."""
        if props.get("Bruksområde", "") == "Gangfelt":
            item["extras"]["highway"] = "crossing"
            item["extras"]["crossing"] = "traffic_signals"
        return True

    _SIGN_DIRECTION_MAP = {
        "Trafikk i metreringsretning": "forward",
        "Trafikk mot metreringsretning": "backward",
        "Tosidig": "both",
    }

    def _extras_skiltplate(self, item: Feature, props: dict) -> bool:
        """Type 96: Skiltplate (Traffic sign plate)."""
        skiltnummer = props.get("Skiltnummer", "")
        if not skiltnummer:
            return False

        # Extract sign code. Example input: "908 - Hindermarkering, høyre", output: "908"
        sign_code = skiltnummer.split(" - ", 1)[0].strip()
        if not sign_code:
            return False

        item["extras"]["traffic_sign"] = f"NO:{sign_code}"

        if facing := props.get("Ansiktsside, rettet mot"):
            if direction := self._SIGN_DIRECTION_MAP.get(facing):
                item["extras"]["direction"] = direction

        if text := props.get("Tekst"):
            item["extras"]["traffic_sign:text"] = text

        belysning = props.get("Belysning", "")
        if belysning in ("Innvendig", "Utvendig"):
            item["extras"]["lit"] = "yes"
        elif belysning == "Ingen":
            item["extras"]["lit"] = "no"

        if leverandor := props.get("Leverandør"):
            item["extras"]["manufacturer"] = leverandor

        return True

    def _extras_jernbanekryssing(self, item: Feature, props: dict) -> bool:
        """Type 100: Jernbanekryssing (Railway crossing)."""
        crossing_type = props.get("Type", "")
        if "I plan" in crossing_type:
            if "uten lysregulering og bommer" in crossing_type:
                item["extras"]["crossing"] = "uncontrolled"
            else:
                if "uten bommer" not in crossing_type or "grind" in crossing_type:
                    item["extras"]["crossing:barrier"] = "yes"
                if "lysregulert" in crossing_type:
                    item["extras"]["crossing:light"] = "yes"
        return True

    # Enum values from NVDB datakatalog type 103 -> OSM traffic_calming values
    _TRAFFIC_CALMING_MAP = {
        "Fartshump": "hump",
        "Fartsputer": "cushion",
        "Innsnevring": "choker",
        "Innsnevring i kryss": "choker",
        "Opphøyd kryssområde": "table",
        "Sideforskyvning": "chicane",
        "Innsnevring og sideforskyvning": "chicane",
        "Rumlefelt": "rumble_strip",
    }

    def _extras_fartsdemper(self, item: Feature, props: dict) -> bool:
        """Type 103: Fartsdemper (Speed bump/hump)."""
        bump_type = props.get("Type", "")
        if osm_type := self._TRAFFIC_CALMING_MAP.get(bump_type):
            if bump_type == "Fartshump":
                if length_str := props.get("Lengde, langs kjøreretning"):
                    try:
                        if float(length_str) >= 7:
                            osm_type = "table"
                    except ValueError:
                        pass
            item["extras"]["traffic_calming"] = osm_type
        return True

    def _extras_vaerstasjon(self, item: Feature, props: dict) -> bool:
        """Type 153: Værstasjon (Weather station)."""
        apply_yes_no(MonitoringTypes.WEATHER, item, True)
        if station_nr := props.get("Målestasjonsnummer"):
            item["extras"]["ref:station"] = station_nr
        return True

    def _extras_kamera(self, item: Feature, _props: dict) -> bool:
        """Type 163: Kamera (Camera)."""
        item["extras"]["surveillance:purpose"] = "traffic"
        return True

    def _extras_gangfelt(self, item: Feature, props: dict) -> bool:
        """Type 174: Gangfelt (Pedestrian crossing)."""
        if props.get("Lysregulert") == "Ja":
            item["extras"]["crossing"] = "traffic_signals"
        elif props.get("Markering av striper", "") != "Ikke striper" or props.get("Skiltet") == "Ja":
            item["extras"]["crossing"] = "uncontrolled"
        else:
            item["extras"]["crossing"] = "unmarked"
        striper = props.get("Markering av striper")
        if striper and striper != "Ikke striper":
            item["extras"]["crossing:markings"] = "zebra"
        if props.get("Trafikkøy") == "Ja":
            item["extras"]["crossing:island"] = "yes"
        if props.get("Hevet") == "Ja":
            item["extras"]["traffic_calming"] = "table"
        if props.get("Belysning") == "Ja":
            item["extras"]["lit"] = "yes"
        return True

    def _extras_nodtelefon(self, item: Feature, _props: dict) -> bool:
        """Type 180: Nødtelefon (Emergency phone)."""
        item["extras"]["amenity"] = "telephone"
        return True

    def _extras_traer(self, item: Feature, props: dict) -> bool:
        """Type 199: Trær (Trees)."""
        tree_type = props.get("Type/gruppering", "")
        if "Allé" in tree_type:
            item["extras"]["natural"] = "tree_row"
        elif "Tregruppe" in tree_type:
            item["extras"]["natural"] = "tree"
        if leaf := props.get("Løvfellende/vintergrønne"):
            if "Løvfellende" in leaf:
                item["extras"]["leaf_cycle"] = "deciduous"
            elif "Vintergrønne" in leaf or "Bartre" in leaf:
                item["extras"]["leaf_cycle"] = "evergreen"
        if count := props.get("Antall"):
            if count != "1":
                item["extras"]["tree_count"] = count
        return True

    def _extras_hydrant(self, item: Feature, props: dict) -> bool:
        """Type 209: Hydrant."""
        if flow_rate := props.get("Kapasitet"):
            item["extras"]["flow_rate"] = f"{flow_rate} l/s"
        return True

    _ANTENNA_TYPE_MAP = {
        "Radio": "radio",
        "Mobiltelefon": "mobile_phone",
    }

    def _extras_antenne(self, item: Feature, props: dict) -> bool:
        """Type 470: Antenne (Antenna)."""
        if antenna_type := props.get("Type"):
            if osm_type := self._ANTENNA_TYPE_MAP.get(antenna_type):
                item["extras"]["communication"] = osm_type
        if height := props.get("Innfestingshøyde"):
            item["extras"]["height"] = f"{height} m"
        return True

    _FIRE_EXTINGUISHER_TYPE_MAP = {
        "Pulverapparat": "powder",
        "Skumapparat": "foam",
        "CO-apparat": "co2",
    }

    def _extras_brannslokningsapparat(self, item: Feature, props: dict) -> bool:
        """Type 213: Brannslokningsapparat (Fire extinguisher)."""
        if extinguisher_type := props.get("Type"):
            if osm_type := self._FIRE_EXTINGUISHER_TYPE_MAP.get(extinguisher_type):
                item["extras"]["fire_extinguisher:type"] = osm_type
        if capacity := props.get("Kapasitet"):
            item["extras"]["capacity"] = f"{capacity} kg"
        if diameter := props.get("Diameter"):
            item["extras"]["diameter"] = diameter
        if props.get("Plassering i teknisk rom") == "Ja":
            item["extras"]["indoor"] = "yes"
        return True

    def _extras_flaggstang(self, item: Feature, props: dict) -> bool:
        """Type 996: Flaggstang (Flagpole)."""
        if height := props.get("Høyde"):
            item["extras"]["height"] = f"{height} m"
        return True

    def _extras_sperring(self, item: Feature, props: dict) -> bool:
        """Type 607: Vegsperring (Road barrier/blocker)."""
        bom_type = props.get("Type", "")
        if bom_type in self._BARRIER_TYPE_MAP:
            item["extras"]["barrier"] = self._BARRIER_TYPE_MAP[bom_type]
        funksjon = props.get("Funksjon", "")
        if funksjon == "Betalingssperre":
            return False
        return True

    def _extras_dognhvileplass(self, item: Feature, props: dict) -> bool:
        """Type 809: Døgnhvileplass (24h truck rest area)."""
        if cap_large := props.get("Antall oppstillingsplasser vogntog"):
            item["extras"]["capacity:hgv"] = cap_large
        if cap_charge := props.get("Antall oppstillingspl. med lading, store kjt."):
            item["extras"]["capacity:hgv:charging"] = cap_charge
        return True

    def _extras_kuldeport(self, item: Feature, _props: dict) -> bool:
        """Type 854: Kuldeport (Cold gate)."""
        item["extras"]["access"] = "yes"
        item["extras"]["note"] = "Kuldeport"
        return True

    def _extras_trapp(self, item: Feature, props: dict) -> bool:
        """Type 875: Trapp (Stairs)."""
        if steps := props.get("Antall trinn"):
            item["extras"]["step_count"] = steps
        if width := props.get("Bredde"):
            item["extras"]["width"] = f"{width} m"
        self._apply_material(item, props)
        if props.get("Barnevognspor") == "Ja":
            item["extras"]["ramp:stroller"] = "yes"
        return True
