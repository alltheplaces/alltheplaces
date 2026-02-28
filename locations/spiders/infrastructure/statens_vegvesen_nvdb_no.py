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

        if type_id == 22:  # Ferist (Cattle grid)
            if material := props.get("Materiale"):
                item["extras"]["material"] = material.lower()

        elif type_id == 23:  # Vegbom (Road barrier)
            barriers = {
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
            bom_type = props.get("Type", "")
            if bom_type in barriers:
                item["extras"]["barrier"] = barriers[bom_type]
            bruk = props.get("Bruksområde", "")
            if bruk == "Gang-/sykkelveg, sluse" and (bom_type == "Annen type vegbom/sperring" or not bom_type):
                item["extras"]["barrier"] = "swing_gate"
            if bruk == "Høyfjellsovergang":
                item["extras"]["access"] = "yes"
                if stedsnavn := props.get("Stedsnavn"):
                    item["name"] = stedsnavn
            # Skip barriers in contexts handled by other types
            if bruk in ("Tunnel", "Bomstasjon", "Ferjekai", "Jernbane"):
                return False

        elif type_id == 25:  # Leskur (Bus shelter)
            if props.get("Innvendig belysning") == "Ja":
                item["extras"]["lit"] = "yes"
            if material := props.get("Materialtype"):
                item["extras"]["material"] = material.lower()
            if props.get("Sittemulighet") == "Ja":
                item["extras"]["bench"] = "yes"

        elif type_id == 37:  # Motorvegkryss (Motorway junction)
            junction_type = props.get("Type", "")
            if "Planskilt kryss" not in junction_type:
                return False
            if ref := props.get("Kryssnummer"):
                item["extras"]["ref"] = str(ref)

        elif type_id == 39:  # Rasteplass (Rest area)
            if cap_small := props.get("Antall oppstillingspl. små kjt."):
                item["extras"]["capacity:car"] = cap_small
            if cap_large := props.get("Antall oppstillingspl. store kjt."):
                item["extras"]["capacity:hgv"] = cap_large
            if props.get("Fast dekke") == "Ja":
                item["extras"]["surface"] = "paved"

        elif type_id == 40:  # Snuplass (Turning point)
            utforming = props.get("Utforming", "")
            if "trafikkøy" in utforming.lower():
                item["extras"]["highway"] = "turning_loop"

        elif type_id == 45:  # Bomstasjon (Toll booth)
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

        elif type_id == 47:  # Møteplass (Passing place)
            bruk = props.get("Bruksområde", "")
            if bruk != "Møteplass":
                return False

        elif type_id == 60:  # Bru (Bridge)
            if length := props.get("Lengde"):
                item["extras"]["length"] = f"{length} m"
            if year := props.get("Byggeår"):
                item["extras"]["start_date"] = year
            # Clean up bridge name like reference nvdb2osm
            if name := item.get("name"):
                item["extras"]["bridge:description"] = name.replace("  ", " ").replace(" Bru", " bru").strip()
            # Detailed bridge structure type mapping from reference
            if bygge_type := props.get("Byggverkstype"):
                bridge_type = bygge_type.lower()
                if "hengebru" in bridge_type:
                    item["extras"]["bridge:structure"] = "suspension"
                elif "bue" in bridge_type or "hvelv" in bridge_type:
                    item["extras"]["bridge:structure"] = "arch"
                elif "fagverk" in bridge_type:
                    item["extras"]["bridge:structure"] = "truss"
                elif bridge_type in ("klaffebru", "svingbru", "rullebru"):
                    item["extras"]["bridge"] = "movable"
                    movable_types = {
                        "klaffebru": "bascule",
                        "svingbru": "swing",
                        "rullebru": "retractable",
                    }
                    if movable := movable_types.get(bridge_type):
                        item["extras"]["bridge:movable"] = movable
                elif bridge_type == "flytebru":
                    item["extras"]["bridge:structure"] = "floating"
                else:
                    item["extras"]["bridge:structure"] = bridge_type

        elif type_id == 64:  # Ferjekai (Ferry terminal)
            # Clean up ferry terminal name (strip Fk/Kai prefixes)
            if name := item.get("name"):
                item["name"] = name.replace("Fk", "").replace("Kai", "").replace("  ", " ").strip()
            if nsr_id := _get_prop(egenskaper, "NSR_Stopplace_ID"):
                item["extras"]["ref:nsrq"] = nsr_id

        elif type_id == 66:  # Skredsikring (Avalanche protector)
            item["extras"]["layer"] = "-1"

        elif type_id == 67:  # Tunnelløp (Tunnel)
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

        elif type_id == 89:  # Signalanlegg (Traffic signals)
            bruk = props.get("Bruksområde", "")
            if bruk == "Gangfelt":
                # Pedestrian crossing signal — override to crossing category
                item["extras"]["highway"] = "crossing"
                item["extras"]["crossing"] = "traffic_signals"

        elif type_id == 100:  # Jernbanekryssing (Railway crossing)
            crossing_type = props.get("Type", "")
            if "I plan" in crossing_type:
                if "uten lysregulering og bommer" in crossing_type:
                    item["extras"]["crossing"] = "uncontrolled"
                else:
                    if "uten bommer" not in crossing_type or "grind" in crossing_type:
                        item["extras"]["crossing:barrier"] = "yes"
                    if "lysregulert" in crossing_type:
                        item["extras"]["crossing:light"] = "yes"

        elif type_id == 103:  # Fartsdemper (Speed bump/hump)
            bump_type = props.get("Type", "")
            type_map = {
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
            if osm_type := type_map.get(bump_type):
                # Fartshump with length >= 7m is a raised table, not a hump
                if bump_type == "Fartshump":
                    if length_str := props.get("Lengde, langs kjøreretning"):
                        try:
                            if float(length_str) >= 7:
                                osm_type = "table"
                        except ValueError:
                            pass
                item["extras"]["traffic_calming"] = osm_type

        elif type_id == 153:  # Værstasjon (Weather station)
            apply_yes_no(MonitoringTypes.WEATHER, item, True)
            if station_nr := props.get("Målestasjonsnummer"):
                item["extras"]["ref:station"] = station_nr

        elif type_id == 162:  # ATK-punkt (Speed enforcement camera)
            pass  # Category tags is all relevant info we have

        elif type_id == 163:  # Kamera (Camera)
            item["extras"]["surveillance:purpose"] = "traffic"

        elif type_id == 174:  # Gangfelt (Pedestrian crossing)
            # Detailed crossing tagging based on nvdb2osm reference
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

        elif type_id == 180:  # Nødtelefon (Emergency phone)
            item["extras"]["amenity"] = "telephone"

        elif type_id == 199:  # Trær (Trees)
            tree_type = props.get("Type/gruppering", "")
            if tree_type == "Enkeltstående":
                pass  # already natural=tree
            elif "Tregruppe" in tree_type or "Allé" in tree_type:
                item["extras"]["natural"] = "tree_row" if "Allé" in tree_type else "tree"
            if phase := props.get("Utviklingsfase"):
                phase_lower = phase.lower()
                if "nyplantet" in phase_lower:
                    item["extras"]["denotation"] = "avenue"
            if leaf := props.get("Løvfellende/vintergrønne"):
                if "Løvfellende" in leaf:
                    item["extras"]["leaf_cycle"] = "deciduous"
                elif "Vintergrønne" in leaf or "Bartre" in leaf:
                    item["extras"]["leaf_cycle"] = "evergreen"
            if count := props.get("Antall"):
                if count != "1":
                    item["extras"]["tree_count"] = count

        elif type_id == 209:  # Hydrant
            placement = props.get("Plassering", "")
            if "Underjordisk" in placement or "Under" in placement:
                item["extras"]["fire_hydrant:type"] = "underground"
            elif "Overgrunn" in placement or "Stolpe" in placement:
                item["extras"]["fire_hydrant:type"] = "pillar"

        elif type_id == 291:  # Viltfare (Animal crossing hazard)
            species_map = {
                "Hjort": "deer",
                "Elg": "moose",
                "Rein": "reindeer",
                "Rådyr": "roe_deer",
            }
            if art := props.get("Art"):
                if species := species_map.get(art):
                    item["extras"]["species:en"] = species

        elif type_id == 607:  # Sperring (Road barrier/blocker)
            barriers = {
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
            bom_type = props.get("Type", "")
            if bom_type in barriers:
                item["extras"]["barrier"] = barriers[bom_type]
            bruk = props.get("Bruksområde", "")
            if bruk == "Gang-/sykkelveg, sluse" and (bom_type == "Annen type vegbom/sperring" or not bom_type):
                item["extras"]["barrier"] = "swing_gate"
            # Skip barriers in contexts handled by other types
            if bruk in ("Tunnel", "Bomstasjon", "Ferjekai", "Jernbane"):
                return False

        elif type_id == 809:  # Døgnhvileplass (24h truck rest area)
            if cap_large := props.get("Antall oppstillingspl. store kjt."):
                item["extras"]["capacity:hgv"] = cap_large
            if cap_charge := props.get("Antall oppstillingspl. med lading, store kjt."):
                item["extras"]["capacity:hgv:charging"] = cap_charge

        elif type_id == 854:  # Kuldeport (Cold gate)
            item["extras"]["access"] = "yes"
            item["extras"]["note"] = "Kuldeport"

        elif type_id == 875:  # Trapp (Stairs)
            if steps := props.get("Antall trinn"):
                item["extras"]["step_count"] = steps
            if width := props.get("Bredde"):
                item["extras"]["width"] = f"{width} m"
            if material := props.get("Materialtype"):
                item["extras"]["material"] = material.lower()
            if props.get("Barnevognsport") == "Ja":
                item["extras"]["ramp:stroller"] = "yes"

        return True
