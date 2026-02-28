import re
from typing import Iterable

import scrapy
from scrapy.http import JsonRequest, Response

from locations.categories import MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature
from locations.licenses import Licenses

# NVDB default pagination size
NVDB_PAGE_SIZE = 750

# NVDB vegobjekttype ID -> OSM category mapping. (https://datakatalogen.atlas.vegvesen.no/)
# Each entry: {type_id: (label, category_dict, name_attr_key_or_None)}
# name_attr_key is the egenskaper "navn" value used to extract a name for the Feature.
OBJECT_TYPE_MAP = {
    22: ("Ferist", {"barrier": "cattle_grid"}, None),
    23: ("Vegbom", {"barrier": "gate"}, None),
    25: ("Leskur", {"amenity": "shelter", "shelter_type": "public_transport"}, None),
    37: ("Motorvegkryss", {"highway": "motorway_junction"}, "Navn"),
    39: ("Rasteplass", {"highway": "rest_area"}, "Navn"),
    40: ("Snuplass", {"highway": "turning_circle"}, None),
    45: ("Bomstasjon", {"barrier": "toll_booth"}, "Navn bomstasjon"),
    47: ("Møteplass", {"highway": "passing_place"}, None),
    60: ("Bru", {"man_made": "bridge"}, "Navn"),
    64: ("Ferjekai", {"amenity": "ferry_terminal"}, "Navn"),
    66: ("Skredsikring", {"tunnel": "avalanche_protector"}, "Navn"),
    67: ("Tunnelløp", {"tunnel": "yes", "man_made": "tunnel"}, "Navn"),
    83: ("Kum", {"man_made": "manhole"}, None),
    87: ("Belysningspunkt", {"highway": "street_lamp", "support": "pole"}, None),
    89: ("Signalanlegg", {"highway": "traffic_signals"}, "Navn"),
    100: ("Jernbanekryssing", {"railway": "level_crossing"}, None),
    103: ("Fartsdemper", {"traffic_calming": "bump"}, None),
    153: ("Værstasjon", {"man_made": "monitoring_station"}, None),
    162: ("ATK-punkt", {"man_made": "surveillance", "surveillance:type": "camera", "enforcement": "maxspeed"}, None),
    163: ("Kamera", {"man_made": "surveillance", "surveillance:type": "camera"}, None),
    174: ("Gangfelt", {"highway": "crossing"}, None),
    180: ("Nødtelefon", {"emergency": "phone"}, None),
    199: ("Trær", {"natural": "tree"}, None),
    209: ("Hydrant", {"emergency": "fire_hydrant"}, None),
    291: ("Viltfare", {"hazard": "animal_crossing"}, None),
    607: ("Sperring", {"barrier": "yes"}, None),
    809: ("Døgnhvileplass", {"highway": "rest_area", "truck": "yes"}, "Navn"),
    854: ("Kuldeport", {"barrier": "roller_shutter"}, None),
    875: ("Trapp", {"highway": "steps"}, None),
}

# Regex to parse WKT POINT geometries: "POINT (x y)" or "POINT Z (x y z)"
WKT_POINT_RE = re.compile(r"POINT\s*Z?\s*\(\s*([-\d.]+)\s+([-\d.]+)")


def _parse_wkt_point(wkt: str) -> tuple[float, float] | None:
    """Parse NVDB WKT POINT geometry string. Returns (lat, lon) or None.

    NVDB API with srid=4326 returns coordinates in EPSG:4326 standard
    axis order: (latitude, longitude).
    """
    if not wkt:
        return None
    m = WKT_POINT_RE.search(wkt)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


# Regex to parse WKT LINESTRING geometries for midpoint extraction
WKT_LINESTRING_RE = re.compile(r"(?:LINESTRING|MULTILINESTRING)\s*Z?\s*\(?\(\s*(.*?)\)", re.DOTALL)


def _parse_wkt_linestring_midpoint(wkt: str) -> tuple[float, float] | None:
    """Extract the midpoint of a WKT LINESTRING for point representation."""
    if not wkt:
        return None
    m = WKT_LINESTRING_RE.search(wkt)
    if not m:
        return None
    coords_str = m.group(1)
    pairs = coords_str.split(",")
    if not pairs:
        return None
    mid = pairs[len(pairs) // 2].strip()
    parts = mid.split()
    if len(parts) >= 2:
        try:
            return float(parts[0]), float(parts[1])
        except ValueError:
            return None
    return None


def _get_prop(egenskaper: list[dict], name: str) -> str | None:
    """Find a property value by its Norwegian name from egenskaper list."""
    for e in egenskaper:
        if e.get("navn") == name:
            v = e.get("verdi")
            # Skip geometry values embedded as properties
            if isinstance(v, str) and (v.startswith("POINT") or v.startswith("LINESTRING") or v.startswith("POLYGON")):
                return None
            return str(v) if v is not None else None
    return None


def _get_props_dict(egenskaper: list[dict]) -> dict[str, str]:
    """Convert egenskaper list to a simple name:value dict, skipping geometry."""
    result = {}
    for e in egenskaper:
        name = e.get("navn", "")
        v = e.get("verdi")
        if v is None:
            continue
        v_str = str(v)
        if v_str.startswith("POINT") or v_str.startswith("LINESTRING") or v_str.startswith("POLYGON"):
            continue
        result[name] = v_str
    return result


class StatensVegvesenNvdbNOSpider(scrapy.Spider):
    """
    Spider for the Norwegian National Road Database (NVDB) API v4,
    operated by Statens vegvesen (Norwegian Public Roads Administration).

    Extracts road infrastructure objects from NVDB and maps them to
    OpenStreetMap-compatible categories including toll booths, bridges,
    tunnels, weather stations, traffic signals, rest areas, pedestrian
    crossings, fire hydrants, trees, and more.

    API documentation: https://nvdb-docs.atlas.vegvesen.no/category/nvdb-api-les-v4/
    """

    name = "statens_vegvesen_nvdb_no"
    allowed_domains = ["nvdbapiles.atlas.vegvesen.no"]
    dataset_attributes = Licenses.NO_NLODv2.value | {
        "attribution:name": "Contains data under the Norwegian licence for Open Government data (NLOD) distributed by Statens vegvesen"
    }

    def start_requests(self) -> Iterable[JsonRequest]:
        for type_id in OBJECT_TYPE_MAP:
            yield JsonRequest(
                url=f"https://nvdbapiles.atlas.vegvesen.no/vegobjekter/api/v4/vegobjekter/{type_id}?inkluder=egenskaper,geometri,lokasjon&srid=4326&antall={NVDB_PAGE_SIZE}",
                headers={"X-Client": "alltheplaces", "Accept": "application/json"},
                cb_kwargs={"type_id": type_id},
            )

    def parse(self, response: Response, type_id: int) -> Iterable[Feature | JsonRequest]:
        data = response.json()
        label, category, name_attr = OBJECT_TYPE_MAP[type_id]

        for obj in data.get("objekter", []):
            item = self._parse_object(obj, type_id, label, category, name_attr)
            if item is not None:
                yield item

        # Follow pagination
        metadata = data.get("metadata", {})
        neste = metadata.get("neste")
        if neste and metadata.get("returnert", 0) > 0:
            next_url = neste.get("href")
            if next_url:
                yield JsonRequest(
                    url=next_url,
                    headers={"X-Client": "alltheplaces", "Accept": "application/json"},
                    cb_kwargs={"type_id": type_id},
                )

    def _parse_object(
        self, obj: dict, type_id: int, label: str, category: dict, name_attr: str | None
    ) -> Feature | None:
        obj_id = obj.get("id")
        if not obj_id:
            return None

        # Extract coordinates from geometry
        geom = obj.get("geometri", {})
        wkt = geom.get("wkt", "")
        coords = _parse_wkt_point(wkt) or _parse_wkt_linestring_midpoint(wkt)

        # Fall back to lokasjon geometry
        if not coords:
            lok_geom = obj.get("lokasjon", {}).get("geometri", {})
            lok_wkt = lok_geom.get("wkt", "")
            coords = _parse_wkt_point(lok_wkt) or _parse_wkt_linestring_midpoint(lok_wkt)

        if not coords:
            return None

        egenskaper = obj.get("egenskaper", [])
        props = _get_props_dict(egenskaper)

        item = Feature()
        item["ref"] = f"NVDB:{type_id}:{obj_id}"
        item["lat"] = coords[0]
        item["lon"] = coords[1]

        # Extract name
        if name_attr:
            name = _get_prop(egenskaper, name_attr)
            if name:
                item["name"] = name

        # Apply OSM category tags
        apply_category(category, item)

        # Apply type-specific extras
        if not self._apply_type_extras(item, type_id, props, egenskaper):
            return None

        # Extract address info from lokasjon
        lokasjon = obj.get("lokasjon", {})
        adresser = lokasjon.get("adresser", [])
        if adresser:
            item["street"] = adresser[0].get("navn")

        return item

    def _apply_type_extras(self, item: Feature, type_id: int, props: dict, egenskaper: list[dict]) -> bool:
        """Apply type-specific OSM tags based on the object type and its properties.
        Returns True if the item should be kept, False to skip it.
        """
        handler = {
            22: self._extras_ferist,
            23: self._extras_vegbom,
            25: self._extras_leskur,
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
            100: self._extras_jernbanekryssing,
            103: self._extras_fartsdemper,
            153: self._extras_vaerstasjon,
            163: self._extras_kamera,
            174: self._extras_gangfelt,
            180: self._extras_nodtelefon,
            199: self._extras_traer,
            209: self._extras_hydrant,
            291: self._extras_viltfare,
            607: self._extras_sperring,
            809: self._extras_dognhvileplass,
            854: self._extras_kuldeport,
            875: self._extras_trapp,
        }.get(type_id)
        if handler is None:
            return True
        return handler(item, props, egenskaper)

    def _extras_ferist(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 22: Ferist (Cattle grid)."""
        if material := props.get("Materiale"):
            item["extras"]["material"] = material.lower()
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

    def _extras_vegbom(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 23: Vegbom (Road barrier)."""
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

    def _extras_leskur(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 25: Leskur (Bus shelter)."""
        if props.get("Innvendig belysning") == "Ja":
            item["extras"]["lit"] = "yes"
        if material := props.get("Materialtype"):
            item["extras"]["material"] = material.lower()
        if props.get("Sittemulighet") == "Ja":
            item["extras"]["bench"] = "yes"
        return True

    def _extras_motorvegkryss(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 37: Motorvegkryss (Motorway junction)."""
        if "Planskilt kryss" not in props.get("Type", ""):
            return False
        if ref := props.get("Kryssnummer"):
            item["extras"]["ref"] = str(ref)
        return True

    def _extras_rasteplass(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 39: Rasteplass (Rest area)."""
        if cap_small := props.get("Antall oppstillingspl. små kjt."):
            item["extras"]["capacity:car"] = cap_small
        if cap_large := props.get("Antall oppstillingspl. store kjt."):
            item["extras"]["capacity:hgv"] = cap_large
        if props.get("Fast dekke") == "Ja":
            item["extras"]["surface"] = "paved"
        return True

    def _extras_snuplass(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 40: Snuplass (Turning point)."""
        if "trafikkøy" in props.get("Utforming", "").lower():
            item["extras"]["highway"] = "turning_loop"
        return True

    def _extras_bomstasjon(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
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

    def _extras_moteplass(self, _item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 47: Møteplass (Passing place)."""
        return props.get("Bruksområde", "") == "Møteplass"

    _BRIDGE_MOVABLE_MAP = {
        "klaffebru": "bascule",
        "svingbru": "swing",
        "rullebru": "retractable",
    }

    def _extras_bru(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
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

    def _extras_ferjekai(self, item: Feature, _props: dict, egenskaper: list[dict]) -> bool:
        """Type 64: Ferjekai (Ferry terminal)."""
        if name := item.get("name"):
            item["name"] = name.replace("Fk", "").replace("Kai", "").replace("  ", " ").strip()
        if nsr_id := _get_prop(egenskaper, "NSR_Stopplace_ID"):
            item["extras"]["ref:nsrq"] = nsr_id
        return True

    def _extras_skredsikring(self, item: Feature, _props: dict, _egenskaper: list[dict]) -> bool:
        """Type 66: Skredsikring (Avalanche protector)."""
        item["extras"]["layer"] = "-1"
        return True

    def _extras_tunnellop(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 67: Tunnelløp (Tunnel)."""
        if length := props.get("Lengde"):
            item["extras"]["tunnel:length"] = f"{length} m"
        if width := props.get("Bredde"):
            item["extras"]["width"] = f"{width} m"
        if height := props.get("Høyde"):
            item["extras"]["maxheight"] = height
        if year := props.get("Åpningsår"):
            item["extras"]["start_date"] = year
        if props.get("Sykkelforbud") == "Ja":
            item["extras"]["bicycle"] = "no"
            item["extras"]["foot"] = "no"
        return True

    def _extras_signalanlegg(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 89: Signalanlegg (Traffic signals)."""
        if props.get("Bruksområde", "") == "Gangfelt":
            item["extras"]["highway"] = "crossing"
            item["extras"]["crossing"] = "traffic_signals"
        return True

    def _extras_jernbanekryssing(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
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

    _TRAFFIC_CALMING_MAP = {
        "Fartshump": "hump",
        "Fartsputer": "cushion",
        "Fartspute": "cushion",
        "Opphøyd gangfelt": "table",
        "Innsnevring": "choker",
        "Innsnevring i kryss": "choker",
        "Opphøyd kryss": "table",
        "Opphøyd kryssområde": "table",
        "Sideforskyvning": "chicane",
        "Innsnevring og sideforskyvning": "chicane",
        "Rumlefelt": "rumble_strip",
    }

    def _extras_fartsdemper(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
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

    def _extras_vaerstasjon(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 153: Værstasjon (Weather station)."""
        apply_yes_no(MonitoringTypes.WEATHER, item, True)
        if station_nr := props.get("Målestasjonsnummer"):
            item["extras"]["ref:station"] = station_nr
        return True

    def _extras_kamera(self, item: Feature, _props: dict, _egenskaper: list[dict]) -> bool:
        """Type 163: Kamera (Camera)."""
        item["extras"]["surveillance:purpose"] = "traffic"
        return True

    def _extras_gangfelt(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 174: Gangfelt (Pedestrian crossing)."""
        if props.get("Trafikklys") == "Ja":
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

    def _extras_nodtelefon(self, item: Feature, _props: dict, _egenskaper: list[dict]) -> bool:
        """Type 180: Nødtelefon (Emergency phone)."""
        item["extras"]["amenity"] = "telephone"
        return True

    def _extras_traer(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
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

    def _extras_hydrant(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 209: Hydrant."""
        placement = props.get("Plassering", "")
        if "Underjordisk" in placement or "Under" in placement:
            item["extras"]["fire_hydrant:type"] = "underground"
        elif "Overgrunn" in placement or "Stolpe" in placement:
            item["extras"]["fire_hydrant:type"] = "pillar"
        return True

    _SPECIES_MAP = {
        "Hjort": "deer",
        "Elg": "moose",
        "Rein": "reindeer",
        "Rådyr": "roe_deer",
    }

    def _extras_viltfare(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 291: Viltfare (Animal crossing hazard)."""
        if art := props.get("Art"):
            if species := self._SPECIES_MAP.get(art):
                item["extras"]["species:en"] = species
        return True

    def _extras_sperring(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 607: Sperring (Road barrier/blocker)."""
        bom_type = props.get("Type", "")
        if bom_type in self._BARRIER_TYPE_MAP:
            item["extras"]["barrier"] = self._BARRIER_TYPE_MAP[bom_type]
        bruk = props.get("Bruksområde", "")
        if bruk == "Gang-/sykkelveg, sluse" and (bom_type == "Annen type vegbom/sperring" or not bom_type):
            item["extras"]["barrier"] = "swing_gate"
        if bruk in ("Tunnel", "Bomstasjon", "Ferjekai", "Jernbane"):
            return False
        return True

    def _extras_dognhvileplass(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 809: Døgnhvileplass (24h truck rest area)."""
        if cap_large := props.get("Antall oppstillingspl. store kjt."):
            item["extras"]["capacity:hgv"] = cap_large
        if cap_charge := props.get("Antall oppstillingspl. med lading, store kjt."):
            item["extras"]["capacity:hgv:charging"] = cap_charge
        return True

    def _extras_kuldeport(self, item: Feature, _props: dict, _egenskaper: list[dict]) -> bool:
        """Type 854: Kuldeport (Cold gate)."""
        item["extras"]["access"] = "yes"
        item["extras"]["note"] = "Kuldeport"
        return True

    def _extras_trapp(self, item: Feature, props: dict, _egenskaper: list[dict]) -> bool:
        """Type 875: Trapp (Stairs)."""
        if steps := props.get("Antall trinn"):
            item["extras"]["step_count"] = steps
        if width := props.get("Bredde"):
            item["extras"]["width"] = f"{width} m"
        if material := props.get("Materialtype"):
            item["extras"]["material"] = material.lower()
        if props.get("Barnevognsport") == "Ja":
            item["extras"]["ramp:stroller"] = "yes"
        return True
