import re
import unicodedata
from datetime import datetime
from urllib.parse import urlparse

from scrapy import Spider
from scrapy.exceptions import CloseSpider
from scrapy.http import JsonRequest

from locations.categories import Categories, Sport, Vending, add_sport, add_vending, apply_category
from locations.items import Feature
from locations.licenses import Licenses

# Pipeline per unit: _build_item filters (invalid, contract,
# test data, excluded subtrees, coords, name) then _apply_name,
# _apply_address (street/comma/place/venue routing), _apply_category
# (table + refine + rescue, generic fallback), _apply_operator,
# _apply_brand, _apply_contact, _apply_media, _apply_lipas_extras,
# _apply_end_date. Dedupe on name+coords+tags+located_in in parse_units
# with count-drift check.
#
# Feed: Helsinki region Service Map (Palvelukartta), api.hel.fi, ~21.5k
# units across Helsinki/Espoo/Vantaa/Kauniainen and neighbouring
# municipalities (Lohja, Kirkkonummi, Siuntio, Inkoo, Raasepori, Vihti)
# plus HUS and wellbeing-area records. Coordinates are [lon, lat] (WGS84). Service nodes form a tree
# (service_nodes.json: id/parent/children); units carry node ids, tabled
# ancestors decide the category via _walk. Scale (Oct 2026): ~15.8k yielded
# POIs. On `tabled/excluded ... missing from tree` warnings the tree moved:
# find the node in service_nodes.json, decide table row vs excluded subtree,
# add it with a test, re-run the harness.
# Sections below, in order:
#   service-node table (precedence = table order)
#   crawl plumbing (departments, service graph, units, dedupe, drift)
#   item assembly and record filters
#   name handling (splits, cleaning, translations)
#   address handling (token parsing, base stripping, fallbacks)
#   operator, brand, contact and parking
#   sport inference and name rescue (untabled units)
#   category refinement (tabled units) and subtags


class HelsinkiServicemapFISpider(Spider):
    """Helsinki region Service Map (Palvelukartta) units."""

    name = "helsinki_servicemap_fi"
    allowed_domains = ["api.hel.fi"]

    # API contents CC BY 4.0. Terms: https://www.hel.fi/palvelukarttaws/restpages/index_en.html
    dataset_attributes = Licenses.CCBY4.value | {
        "attribution:name": "Contains Service Map (Palvelukartta) data, City of Helsinki as administrator",
        "attribution:website": "https://www.hel.fi/palvelukarttaws/restpages/index_en.html",
    }

    api_base_url = "https://api.hel.fi/servicemap/v2"
    page_size = 1000

    custom_settings = {"DOWNLOAD_TIMEOUT": 60, "RETRY_TIMES": 5}

    # A unit can match several nodes; the earliest row wins. Real facilities
    # on top, parking at the bottom, or a playground with a car park tags
    # as parking. IDs as of Oct 2026. To add a row, append near its semantic
    # group (never reorder existing rows): position decides multi-filed units
    # (clinic+school keeps the earlier school row). Precedence pinned by
    # pairwise assertions in test_table_order_frozen.
    SERVICE_NODES = {
        1097: (Categories.SCHOOL, {}),  # Perusopetus (basic education)
        1257: (Categories.SCHOOL, {}),  # Lukiokoulutus (upper secondary school)
        1336: (Categories.SCHOOL, {}),  # Aikuisten perus- ja lukiokoulutus (adult education)
        868: (Categories.KINDERGARTEN, {}),  # Lasten päivähoito (daycare)
        1088: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        2118: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        879: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        887: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        895: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        903: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        911: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        919: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        935: (Categories.KINDERGARTEN, {}),  # Esiopetus (preschool)
        871: (Categories.KINDERGARTEN, {}),  # Päivähoito (daycare)
        870: (Categories.KINDERGARTEN, {}),  # Suomenkielinen päivähoito (daycare in Finnish)
        881: (Categories.KINDERGARTEN, {}),  # Ruotsinkielinen päivähoito (daycare in Swedish)
        882: (Categories.KINDERGARTEN, {}),  # Päivähoito (daycare)
        905: (Categories.KINDERGARTEN, {}),  # Englanninkielinen päivähoito (daycare in English)
        906: (Categories.KINDERGARTEN, {}),  # Päivähoito (daycare)
        875: (Categories.KINDERGARTEN, {}),  # Erityisryhmä (special group)
        963: (Categories.KINDERGARTEN, {}),  # Suomenkielinen ryhmäperhepäivähoito (Finnish group family daycare)
        2125: (Categories.KINDERGARTEN, {}),  # Päivähoidon järjestämä esiopetus (daycare preschool)
        1090: (Categories.KINDERGARTEN, {}),  # Päivähoidon järjestämä esiopetus (daycare preschool)
        1089: (Categories.KINDERGARTEN, {}),  # Suomen- ja vieraskielinen esiopetus (Finnish/other-language preschool)
        2122: (Categories.KINDERGARTEN, {}),  # Suomen- ja vieraskielinen esiopetus (Finnish/other-language preschool)
        1093: (Categories.KINDERGARTEN, {}),  # Ruotsinkielinen esiopetus (preschool in Swedish)
        2126: (Categories.KINDERGARTEN, {}),  # Ruotsinkielinen esiopetus (preschool in Swedish)
        2129: (Categories.KINDERGARTEN, {}),  # Päivähoidon järjestämä esiopetus (daycare preschool)
        1094: (Categories.KINDERGARTEN, {}),  # Päivähoidon järjestämä esiopetus (daycare preschool)
        324: (Categories.LIBRARY, {}),  # Kirjastot (libraries)
        345: (Categories.LIBRARY, {}),  # Kirjastot (libraries)
        2197: (Categories.LIBRARY, {}),  # Yliopistojen kirjastot (university libraries)
        2194: (Categories.LIBRARY, {}),  # Yliopistojen kirjastot (university libraries)
        1356: (Categories.COLLEGE, {}),  # Ammattikorkeakoulut (universities of applied sciences)
        2180: (Categories.COLLEGE, {}),  # Suomenkielinen ammatillinen peruskoulutus (Finnish vocational education)
        2181: (Categories.COLLEGE, {}),  # Suomenkielinen ammatillinen lisäkoulutus (vocational further education)
        1361: (Categories.COLLEGE, {}),  # Suomenkielinen työväenopisto (Finnish workers' institute)
        1365: (Categories.COLLEGE, {}),  # Ruotsinkielinen työväenopisto (Swedish workers' institute)
        2212: (Categories.COLLEGE, {}),  # Kansalaisopisto (civic institute, adult education)
        1371: (Categories.COLLEGE, {}),  # Kansanopisto (folk high school)
        1073: (Categories.SCHOOL, {}),  # Pelastuskoulu (rescue school)
        340: (Categories.COMMUNITY_CENTRE, {}),  # Kurssimuotoista tietokoneopetusta (computer courses)
        1363: (Categories.COLLEGE, {}),  # Opetuspaikat (teaching venues)
        1367: (Categories.COLLEGE, {}),  # Opetuspaikat (teaching venues)
        1359: (Categories.UNIVERSITY, {}),  # Yliopistot (universities)
        1370: (Categories.MUSIC_SCHOOL, {}),  # Musiikkiopisto (music schools)
        2409: (Categories.MUSIC_SCHOOL, {}),  # Musiikkikoulu (music schools)
        468: (Categories.MUSIC_SCHOOL, {}),  # Soitonopetus (instrument lessons)
        2398: (Categories.MUSIC_SCHOOL, {}),  # Bändikoulu (band schools)
        1009: (Categories.HOSPITAL, {}),  # Sairaalat (hospitals)
        1010: (Categories.HOSPITAL, {}),  # Yliopistolliset sairaalat (university hospitals)
        1012: (Categories.HOSPITAL, {}),  # Kaupunginsairaalat (city hospitals)
        1000: (Categories.CLINIC_URGENT, {}),  # Päivystys (emergency departments)
        1001: (Categories.CLINIC_URGENT, {}),  # Aikuisten terveyskeskuspäivystys (adult clinic emergency care)
        991: (Categories.CLINIC, {}),  # Terveysasemat (health stations)
        992: (Categories.CLINIC, {}),  # Lääkärin vastaanotto (doctor receptions)
        1021: (Categories.CLINIC, {}),  # HUS:n erikoissairaanhoito (HUS specialised care)
        1004: (
            Categories.CLINIC,
            {"healthcare:speciality": "maternal_and_child_health"},
        ),  # Neuvolat (maternity and child-health clinics)
        1008: (
            Categories.CLINIC,
            {"healthcare:speciality": "maternal_and_child_health"},
        ),  # Äitiysneuvola (maternity clinics)
        1005: (
            Categories.CLINIC,
            {"healthcare:speciality": "maternal_and_child_health"},
        ),  # Lastenneuvola (child-health clinics)
        1006: (Categories.CLINIC, {}),  # Perhesuunnittelu (family planning)
        1023: (Categories.CLINIC, {}),  # Psykiatrian poliklinikat (psychiatric outpatient clinics)
        1054: (
            Categories.CLINIC,
            {"healthcare:speciality": "addiction"},
        ),  # Päihdehuollon polikliininen hoito (substance-abuse outpatient care)
        1055: (Categories.CLINIC, {"healthcare:speciality": "addiction"}),  # Korvaushoito (substitution treatment)
        1058: (Categories.CLINIC, {"healthcare:speciality": "addiction"}),  # Päihdehuollon katkaisuhoito (detox units)
        1007: (Categories.CLINIC, {}),  # Kehitysvammapoliklinikka (developmental-disability clinics)
        1031: (Categories.CLINIC, {}),  # Fysioterapia (physiotherapy)
        1038: (Categories.CLINIC, {}),  # Toimintaterapia (occupational therapy)
        1017: (Categories.MEDICAL_LABORATORY, {}),  # Laboratorio (laboratories)
        1018: (Categories.MEDICAL_IMAGING, {}),  # Röntgen (x-ray clinics)
        1036: (Categories.SPEECH_THERAPIST, {}),  # Puheterapia (speech therapy)
        995: (Categories.DENTIST, {}),  # Hammashoito (dental care)
        1040: (Categories.PODIATRIST, {}),  # Jalkaterapia (foot therapy)
        990: (Categories.PHARMACY, {}),  # Apteekki (pharmacies)
        2164: (
            Categories.NURSE_CLINIC,
            {"healthcare:speciality": "community;paediatrics"},
        ),  # Kouluterveydenhuolto (school health care)
        2165: (
            Categories.NURSE_CLINIC,
            {"healthcare:speciality": "community;paediatrics"},
        ),  # Kouluterveydenhuolto (school health care)
        2166: (
            Categories.NURSE_CLINIC,
            {"healthcare:speciality": "community"},
        ),  # Opiskeluterveydenhuolto (student health care)
        2167: (
            Categories.NURSE_CLINIC,
            {"healthcare:speciality": "community"},
        ),  # Opiskeluterveydenhuolto (student health care)
        2309: (Categories.NURSE_CLINIC, {}),  # Sairaanhoitajan vastaanotto (nurse receptions)
        2310: (Categories.NURSE_CLINIC, {}),  # Diabeteshoitajan vastaanotto (diabetes nurse receptions)
        993: (Categories.NURSE_CLINIC, {}),  # Terveydenhoitajan vastaanotto (nurse clinics)
        1072: (Categories.FIRE_STATION, {}),  # Pelastusasemat (fire stations)
        1074: (Categories.FIRE_STATION, {}),  # Sopimuspalokunnat (volunteer fire brigades)
        1077: (Categories.POLICE, {}),  # Poliisilaitokset ja -asemat (police stations)
        781: (Categories.COURTHOUSE, {}),  # Tuomioistuimet (courts)
        520: (Categories.TRAIN_STATION, {}),  # Rautatieasemat (railway stations)
        519: (Categories.TRAIN_STATION, {"station": "subway"}),  # Metroasemat (metro stations)
        545: (Categories.FERRY_TERMINAL, {}),  # Terminaalit (ferry terminals)
        362: (Categories.MUSEUM, {}),  # Museot (museums)
        745: (Categories.MUSEUM, {}),  # Museot (museums)
        360: (Categories.THEATRE, {}),  # Teatterit (theatres)
        752: (Categories.THEATRE, {}),  # Teatterit (theatres)
        2154: (Categories.THEATRE, {}),  # Teatteri (theatre)
        353: (Categories.CINEMA, {}),  # Elokuvateatterit (cinemas)
        68: (Categories.LEISURE_PLAYGROUND, {}),  # Leikkipuistot (playgrounds)
        499: (Categories.LEISURE_PLAYGROUND, {}),  # Leikkipuistot (playgrounds)
        501: (Categories.LEISURE_PLAYGROUND, {}),  # Leikkipaikat ei ohjattua toimintaa (unsupervised play areas)
        70: (Categories.LEISURE_PLAYGROUND, {}),  # Leikkipaikat ei ohjattua toimintaa (unsupervised play areas)
        154: (Categories.COMMUNITY_CENTRE, {}),  # Nuorisotilat (youth rooms)
        263: (Categories.COMMUNITY_CENTRE, {}),  # Nuorisotilat (youth rooms)
        510: (Categories.COMMUNITY_CENTRE, {}),  # Nuorisotilat (youth rooms)
        366: (Categories.COMMUNITY_CENTRE, {}),  # Nuorisotalot (youth centres)
        375: (Categories.COMMUNITY_CENTRE, {}),  # Avoin nuorisotoiminta (open youth activities)
        341: (Categories.COMMUNITY_CENTRE, {}),  # Opastusta tietokoneen käyttöön (digital guidance)
        847: (Categories.COMMUNITY_CENTRE, {}),  # Alueellinen kumppanuustyö (community partnership)
        490: (Categories.OFFICE_GOVERNMENT, {}),  # Nuorten neuvonta ja ohjaus (youth guidance)
        449: (Categories.COMMUNITY_CENTRE, {}),  # Poikakerho / poikaryhmät (boys' clubs)
        480: (Categories.COMMUNITY_CENTRE, {}),  # Tyttökerho / tyttöryhmät (girls' clubs)
        1334: (Categories.SOCIAL_FACILITY, {}),  # Nuorten työpajatoiminta (youth workshops)
        611: (Categories.GYM, {}),  # Kuntosali (gyms)
        415: (Categories.GYM, {}),  # Kuntosali (gyms)
        2219: (Categories.GYM, {}),  # Seniorikuntosalit (senior gyms)
        610: (Categories.GYM, {}),  # Kuntokeskus (fitness centres)
        632: (
            Categories.LEISURE_PITCH,
            {"sport": Sport.ATHLETICS},
        ),  # Yksittäinen yleisurheilun suorituspaikka (athletics spots)
        614: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Liikuntahallit (sports halls)
        556: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.EQUESTRIAN}),  # Ratsastusmaneesi (riding manege)
        609: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.MARTIAL_ARTS}),  # Kamppailulajien sali (martial arts)
        631: (Categories.LEISURE_SPORTS_HALL, {}),  # Telinevoimistelutila (gymnastics halls)
        2431: (
            Categories.LEISURE_TRACK,
            {"sport": Sport.EQUESTRIAN},
        ),  # Ovaalirata (harness-racing ovals)
        # Sports hall, distinct from the gym rooms above.
        612: (Categories.LEISURE_SPORTS_HALL, {}),  # Liikuntasali (sports hall)
        616: (Categories.LEISURE_SPORTS_HALL, {}),  # Liikuntahalli (sports hall building)
        623: (Categories.LEISURE_SPORTS_HALL, {"sport": Sport.TENNIS}),  # Tennishalli (tennis halls)
        619: (Categories.LEISURE_SPORTS_HALL, {"sport": Sport.FLOORBALL}),  # Salibandyhalli (floorball halls)
        2357: (Categories.LEISURE_SPORTS_HALL, {"sport": Sport.PADEL}),  # Padelhalli (padel halls)
        607: (Categories.LEISURE_BOWLING_ALLEY, {}),  # Keilahalli (bowling halls)
        617: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Monitoimihalli / areena (multipurpose halls)
        626: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.PARKOUR}),  # Parkour-Sali (parkour halls)
        620: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.SKATEBOARD}),  # Skeittihalli (skate halls)
        629: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Sisäkiipeilyseinä (indoor climbing walls)
        2427: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Vesiurheilukeskus (water sports centre)
        678: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Koskimelontakeskus (whitewater canoe centres)
        647: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Liikuntapuisto (sports parks)
        686: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.SWIMMING}),  # Maauimala (outdoor pools)
        693: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.SWIMMING}),  # Uimahalli (swimming halls)
        692: (
            Categories.LEISURE_SPORTS_HALL,
            {"sport": Sport.SWIMMING},
        ),  # Uima-allas (school swimming pools)
        155: (Categories.SAUNA, {}),  # Tilaussaunat (rental saunas)
        264: (Categories.SAUNA, {}),  # Tilaussaunat (rental saunas)
        511: (Categories.SAUNA, {}),  # Tilaussaunat (rental saunas)
        2168: (Categories.SAUNA, {}),  # Hyvän olon palvelut (wellness services)
        687: (Categories.LEISURE_SWIMMING_AREA, {}),  # Talviuintipaikka (winter swimming spots)
        688: (Categories.NATURAL_BEACH, {}),  # Uimapaikka (swimming places)
        689: (Categories.NATURAL_BEACH, {}),  # Uimaranta (beaches)
        61: (Categories.LEISURE_PADDLING_POOL, {}),  # Kahluualtaat (paddling pools)
        492: (Categories.LEISURE_PADDLING_POOL, {}),  # Kahluualtaat (paddling pools)
        603: (Categories.LEISURE_ICE_RINK, {}),  # Harjoitusjäähalli (practice ice halls)
        604: (Categories.LEISURE_ICE_RINK, {}),  # Kilpajäähalli (competition ice halls)
        2418: (Categories.LEISURE_DANCE, {}),  # Tanssikoulu (dance schools)
        630: (Categories.LEISURE_DANCE, {}),  # Tanssitila (dance spaces)
        359: (Categories.LEISURE_DANCE, {}),  # Tanssitilat (dance spaces)
        473: (Categories.LEISURE_DANCE, {}),  # Tanssi (dance)
        654: (Categories.LEISURE_PITCH, {}),  # Pallokentät (ball fields)
        # Bare pitch: names supply sport and surface (cf. Tenniskenttä,
        # Hiekkatekonurmikenttä); indoor halls co-filed with courts keep
        # theirs (cf. Talin Tenniskeskus units filed under both 614 halls
        # and 662 courts, earliest-wins by table order).
        # Redundant with the 654 inheritance today, but explicit: 662's
        # parent chain currently resolves to tabled 654 via _walk (see
        # _build_service_graph), so dropping this row would silently move
        # tennis areas to whatever 654 maps. The mapping survives Service
        # Map tree changes.
        662: (Categories.LEISURE_PITCH, {}),  # Tenniskenttäalue (tennis court areas)
        554: (Categories.LEISURE_PITCH, {"sport": Sport.EQUESTRIAN}),  # Esteratsastuskenttä (show-jumping grounds)
        555: (Categories.LEISURE_PITCH, {"sport": Sport.EQUESTRIAN}),  # Ratsastuskenttä (riding fields)
        642: (Categories.LEISURE_ICE_RINK, {"sport": Sport.ICE_SKATING}),  # Luistelukenttä (skating rinks)
        641: (Categories.LEISURE_PITCH, {"sport": Sport.ICE_HOCKEY}),  # Kaukalo (hockey rinks)
        644: (Categories.LEISURE_PITCH, {"sport": Sport.ICE_SKATING}),  # Pikaluistelurata (speed-skating tracks)
        645: (Categories.LEISURE_PITCH, {"sport": Sport.ICE_SKATING}),  # Tekojääkenttä (artificial ice fields)
        652: (Categories.LEISURE_PITCH, {"sport": Sport.SKATEBOARD}),  # Skeitti / rullaluistelupaikka (skate parks)
        2356: (Categories.LEISURE_PITCH, {"sport": Sport.TABLE_TENNIS}),  # Pöytätennisalue (table-tennis areas)
        578: (Categories.LEISURE_DISC_GOLF_COURSE, {}),  # Frisbeegolf-rata (disc golf courses)
        637: (Categories.LEISURE_GOLF_COURSE, {}),  # Golfkenttä (golf courses)
        664: (Categories.LEISURE_PITCH, {"sport": Sport.ATHLETICS}),  # Yleisurheilukenttä (athletics fields)
        665: (
            Categories.LEISURE_PITCH,
            {"sport": Sport.ATHLETICS},
        ),  # Yleisurheilun harjoitusalue (athletics training areas)
        649: (Categories.LEISURE_PITCH, {"sport": Sport.PARKOUR}),  # Parkour- alue (parkour areas)
        651: (Categories.LEISURE_TRACK, {"sport": Sport.CYCLING}),  # Pyöräilyrata (cycling tracks, cf. velodromes)
        574: (Categories.LEISURE_PITCH, {"sport": Sport.CLIMBING}),  # Ulkokiipeilypaikka (outdoor climbing venues)
        650: (Categories.LEISURE_TRACK, {"sport": Sport.CYCLING}),  # Pyöräilyalue (cycling areas, cf. BMX tracks)
        670: (Categories.LEISURE_TRACK, {"sport": Sport.KARTING}),  # Karting-rata (kart circuits)
        659: (Categories.LEISURE_PITCH, {}),  # Pallokenttä (ball fields)
        658: (Categories.LEISURE_PITCH, {"sport": Sport.VOLLEYBALL}),  # Lentopallokenttä (volleyball fields)
        657: (Categories.LEISURE_PITCH, {"sport": Sport.BASKETBALL}),  # Koripallokenttä (basketball courts)
        655: (Categories.LEISURE_PITCH, {"sport": Sport.BEACH_VOLLEYBALL}),  # Beachvolleykenttä (beach volleyball)
        2355: (Categories.LEISURE_PITCH, {"sport": Sport.PADEL}),  # Padelkenttäalue (padel court areas)
        661: (Categories.LEISURE_PITCH, {}),  # Rullakiekkokenttä (roller-hockey rinks)
        656: (Categories.LEISURE_PITCH, {"sport": Sport.SOCCER}),  # Jalkapallostadionit (football stadiums)
        660: (Categories.LEISURE_PITCH, {"sport": Sport.BASEBALL}),  # Pesäpallostadion (pesäpallo stadiums)
        627: (Categories.LEISURE_PITCH, {"sport": Sport.TABLE_TENNIS}),  # Pöytätennistila (table-tennis rooms)
        613: (Categories.LEISURE_FITNESS_STATION, {}),  # Voimailusali (weight-training rooms)
        696: (Categories.LEISURE_FISHING, {}),  # Kalastusalue / -paikka (fishing areas)
        2439: (Categories.LEISURE_FITNESS_STATION, {}),  # Ulkokuntosali (outdoor gym)
        653: (Categories.LEISURE_FITNESS_STATION, {}),  # Ulkokuntoiluvälineet (outdoor fitness equipment)
        648: (Categories.LEISURE_FITNESS_STATION, {}),  # Lähiliikuntapaikka (neighbourhood exercise grounds)
        2441: (Categories.LEISURE_FITNESS_STATION, {}),  # Kuntoportaat (fitness stairs)
        2440: (Categories.LEISURE_FITNESS_STATION, {}),  # Ulkokuntoilupaikka (outdoor exercise areas)
        17: (Categories.LEISURE_DOG_PARK, {}),  # Koira-aitaukset (dog enclosures)
        63: (Categories.LEISURE_DOG_PARK, {}),  # Koira-aitaukset (dog enclosures)
        494: (Categories.LEISURE_DOG_PARK, {}),  # Koira-aitaukset (dog enclosures)
        20: (Categories.LEISURE_DOG_PARK, {}),  # Koirauimarannat (dog beaches)
        66: (Categories.LEISURE_DOG_PARK, {}),  # Koirauimarannat (dog beaches)
        94: (Categories.TOILETS, {}),  # Yleisövessat (public toilets)
        1083: (
            Categories.SHELTER,
            {"shelter_type": "bomb_shelter"},
        ),  # Väestönsuojat (civil-defence shelters; amenity=shelter per the
        # shelter_type=bomb_shelter wiki — military=bunker is disputed for
        # civilian use, so it stays out)
        497: (Categories.LEISURE_DOG_PARK, {}),  # Koirauimarannat (dog beaches)
        2008: (Categories.LEISURE_DOG_PARK, {}),  # Koiraurheilualue (dog sports areas)
        19: (Categories.LEISURE_DOG_PARK, {}),  # Koirametsät (dog forests)
        65: (Categories.LEISURE_DOG_PARK, {}),  # Koirametsät (dog forests)
        496: (Categories.LEISURE_DOG_PARK, {}),  # Koirametsät (dog forests)
        21: (Categories.LEISURE_DOG_PARK, {}),  # Opaskoira-aitaukset (guide-dog pens)
        498: (Categories.LEISURE_DOG_PARK, {}),  # Opaskoira-aitaukset (guide-dog pens)
        67: (Categories.LEISURE_DOG_PARK, {}),  # Opaskoira-aitaukset (guide-dog pens)
        714: (Categories.LEISURE_PARK, {}),  # Ulkoilualue (outdoor areas)
        708: (Categories.LEISURE_NATURE_RESERVE, {}),  # Kansallispuisto (national parks)
        57: (Categories.LEISURE_NATURE_RESERVE, {}),  # Luonnonsuojelu (nature conservation)
        712: (
            Categories.LEISURE_NATURE_RESERVE,
            {},
        ),  # Muu luonnonsuojelualue, jolla on virkistyspalveluita (nature reserves)
        701: (Categories.TOURISM_PICNIC_SITE, {}),  # Ruoanlaittopaikka (cooking places)
        697: (Categories.SHELTER, {}),  # Laavu, kota tai kammi (lean-tos and huts)
        703: (Categories.SHELTER, {}),  # Tupa (huts)
        59: (Categories.CARPET_WASHING, {}),  # Matonpesupaikat (carpet-washing places)
        361: (Categories.CARPET_WASHING, {}),  # Matonpesupaikat (carpet-washing places)
        546: (Categories.MARINA, {}),  # Venesatamat (marinas)
        705: (Categories.MARINA, {}),  # Venesatama (marina)
        2142: (Categories.MARINA, {}),  # Venesatamat (marinas)
        2198: (Categories.MOORING, {}),  # Veneiden lyhytaikainen kiinnittyminen (short-term moorings)
        2199: (Categories.MOORING, {}),  # Veneiden lyhytaikainen kiinnittyminen (short-term moorings)
        825: (Categories.NURSING_HOME, {}),  # Iäkkäiden ympärivuorokautinen palveluasuminen (elderly care housing)
        826: (Categories.NURSING_HOME, {}),  # Iäkkäiden laitospalvelu (elderly institutional care)
        2446: (Categories.MORTUARY, {}),  # Vainajatilat (mortuaries)
        # Care services delivered off-site, not offices. Rule of thumb for
        # the next neuvonta/ohjaus/palvelu node: a desk the public visits
        # (neuvonta, ohjaamo, customer service) is OFFICE_GOVERNMENT; care
        # delivered at the client's home/school (kotihoito, sosiaalityö,
        # perhetyö) is SOCIAL_FACILITY; a bookable room for activities is
        # COMMUNITY_CENTRE or EVENTS_VENUE. _civic_category encodes the
        # desk half; the table encodes the rest per node.
        793: (Categories.SOCIAL_FACILITY, {}),  # Perheneuvonta ja perheneuvolatoiminta (family counselling)
        829: (Categories.SOCIAL_FACILITY, {}),  # Kotihoito (home care)
        996: (Categories.SOCIAL_FACILITY, {}),  # Kotihoito (home care)
        846: (Categories.SOCIAL_FACILITY, {}),  # Aikuisten sosiaalityö (adult social work, delivered care)
        2373: (Categories.SOCIAL_FACILITY, {}),  # Iäkkäiden kotipalvelu (elderly home service)
        2319: (Categories.SOCIAL_FACILITY, {}),  # Lapsiperheiden sosiaalipalveluiden asiakasohjaus (family guidance)
        2311: (Categories.SOCIAL_FACILITY, {}),  # Lapsiperheiden palvelutarpeen arviointi (family needs assessment)
        788: (Categories.SOCIAL_FACILITY, {}),  # Lastensuojelun sosiaalityö (child-welfare social work, delivered care)
        792: (Categories.OFFICE_GOVERNMENT, {}),  # Lapsiperheiden sosiaaliohjaus (family social guidance)
        2189: (Categories.OFFICE_GOVERNMENT, {}),  # Perhekeskukset (family centres)
        796: (Categories.OFFICE_GOVERNMENT, {}),  # Perheoikeudelliset palvelut (family-law services)
        2335: (Categories.SOCIAL_FACILITY, {}),  # Lastensuojelun palveluiden asiakasohjaus (child-welfare guidance)
        2312: (Categories.OFFICE_GOVERNMENT, {}),  # Perhesosiaalityö (family social work)
        2390: (Categories.SOCIAL_FACILITY, {}),  # Vammaispalvelun lyhytaikainen huolenpito (short-term respite care)
        848: (Categories.OFFICE_GOVERNMENT, {}),  # Aikuisten sosiaaliohjaus (adult social guidance)
        850: (Categories.SOCIAL_FACILITY, {}),  # Työhön kuntoutus- ja työllistämispalvelut (employment rehab)
        851: (Categories.SOCIAL_FACILITY, {}),  # Kuntouttava työtoiminta (rehabilitative work)
        2375: (Categories.SOCIAL_FACILITY, {}),  # Sosiaalinen kuntoutus (social rehabilitation)
        856: (Categories.OFFICE_GOVERNMENT, {}),  # Sovittelutoiminta (mediation services)
        867: (Categories.SOCIAL_FACILITY, {}),  # Ruoka-apu (food aid)
        2383: (Categories.SOCIAL_FACILITY, {}),  # Asunnottomien palvelukeskustoiminta (homeless service centres)
        822: (Categories.SOCIAL_FACILITY, {}),  # Iäkkäiden päivätoiminta (elderly day activities)
        823: (Categories.SOCIAL_FACILITY, {}),  # Iäkkäiden palvelukeskustoiminta (elderly service centres)
        802: (Categories.SOCIAL_FACILITY, {}),  # Vammaispalvelun päivätoiminta (disability day activities)
        813: (Categories.SOCIAL_FACILITY, {}),  # Kehitysvammahuollon päivätoiminta (developmental-care day activities)
        814: (Categories.SOCIAL_FACILITY, {}),  # Kehitysvammahuollon työllistämispalvelut (sheltered employment)
        2307: (Categories.CLINIC, {}),  # Mielenterveyspalvelujen avohoito (mental-health outpatient care)
        2308: (Categories.SOCIAL_FACILITY, {}),  # Ehkäisevä päihdetyö (preventive substance-abuse work)
        1052: (Categories.SOCIAL_FACILITY, {}),  # Päihdehuollon sosiaalityö (substance-abuse social work)
        1053: (Categories.SOCIAL_FACILITY, {}),  # Päihdehuollon sosiaaliohjaus (substance-abuse guidance)
        1056: (Categories.SOCIAL_FACILITY, {}),  # Päihdehuollon päivätoiminta (substance-abuse day activities)
        803: (
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home", "social_facility:for": "disabled"},
        ),  # Vammaispalvelun asumispalvelut (disability housing services)
        852: (Categories.SOCIAL_FACILITY, {}),  # Muun sosiaalihuollon asumispalvelut (social-care housing services)
        2442: (Categories.SOCIAL_FACILITY, {}),  # Vammaispalvelun yhteisöllinen asuminen (communal disability housing)
        815: (Categories.SOCIAL_FACILITY, {}),  # Kehitysvammahuollon asumispalvelut (developmental-care housing)
        816: (Categories.SOCIAL_FACILITY, {}),  # Kehitysvammahuollon laitospalvelu (developmental-care institutions)
        1057: (Categories.SOCIAL_FACILITY, {}),  # Päihdehuollon asumispalvelut (substance-abuse housing)
        2160: (
            Categories.SOCIAL_FACILITY,
            {},
        ),  # Mielenterveyskuntoutujien asumispalvelut (mental-health rehab housing)
        1024: (Categories.SOCIAL_FACILITY, {}),  # Psykiatrinen asumiskuntoutus (psychiatric housing rehab)
        824: (Categories.SOCIAL_FACILITY, {}),  # Iäkkäiden itsenäinen asuminen (independent elderly housing)
        2447: (
            Categories.SOCIAL_FACILITY,
            {},
        ),  # Mielenterveyskuntoutujien yhteisöllinen asuminen (communal rehab housing)
        2443: (Categories.SOCIAL_FACILITY, {}),  # Yhteisöllinen asuminen (communal housing)
        2376: (Categories.SOCIAL_FACILITY, {}),  # Iäkkäiden yhteisöllinen asuminen (communal elderly housing)
        789: (Categories.SOCIAL_FACILITY, {}),  # Lastensuojelun laitospalvelu (residential child welfare)
        2334: (Categories.SOCIAL_FACILITY, {}),  # Ympärivuorokautinen perhekuntoutus (residential family rehab)
        2331: (Categories.SOCIAL_FACILITY, {}),  # Tehostettu perhetyö (intensive family work)
        2325: (Categories.SOCIAL_FACILITY, {}),  # Lasten ja nuorten vastaanottolaitokset (reception institutions)
        2326: (Categories.SOCIAL_FACILITY, {}),  # Lastenkotitoiminta (children's homes)
        736: (Categories.HOTEL, {}),  # Hotellit ja majoitus (hotels and accommodation)
        738: (Categories.CAFE, {}),  # Kahvilat (cafes)
        726: (Categories.CAFE, {}),  # Kahvila (cafe)
        751: (Categories.RESTAURANT, {}),  # Ravintolat (restaurants)
        729: (Categories.RESTAURANT, {}),  # Ravintola (restaurant)
        2174: (Categories.BAR, {}),  # Baarit ja yöelämä (bars and nightlife)
        183: (Categories.CANTEEN, {}),  # Henkilöstöravintolat (staff restaurants)
        737: (Categories.EVENTS_VENUE, {}),  # Juhlatilat (party rooms)
        152: (Categories.EVENTS_VENUE, {}),  # Juhlatilat (party rooms)
        261: (Categories.EVENTS_VENUE, {}),  # Juhlatilat (party rooms)
        508: (Categories.EVENTS_VENUE, {}),  # Juhlatilat (party rooms)
        2173: (Categories.EVENTS_VENUE, {}),  # Tapahtumapaikat (event venues)
        742: (Categories.EVENTS_VENUE, {}),  # Kokouspaikat (meeting rooms)
        151: (Categories.EVENTS_VENUE, {}),  # Kokouspaikat (meeting rooms)
        260: (Categories.EVENTS_VENUE, {}),  # Kokouspaikat (meeting rooms)
        507: (Categories.EVENTS_VENUE, {}),  # Kokouspaikat (meeting rooms)
        2208: (Categories.EVENTS_VENUE, {}),  # Asukastilat (resident rooms)
        2209: (Categories.EVENTS_VENUE, {}),  # Asukastilat (resident rooms)
        2210: (Categories.EVENTS_VENUE, {}),  # Asukastilat (resident rooms)
        354: (Categories.THEATRE, {}),  # Konserttitilat (concert halls)
        710: (Categories.CARAVAN_SITE, {}),  # Matkailupalveluiden alue (caravan areas)
        702: (Categories.TOURISM_CAMP_SITE, {}),  # Telttailu ja leiriytyminen (camp sites)
        344: (
            Categories.LEISURE_GARDEN,
            {"garden:type": "botanical"},
        ),  # Kasvitieteelliset puutarhat (botanical gardens)
        749: (Categories.TOURISM_ATTRACTION, {}),  # Nähtävyydet (sights)
        2245: (Categories.TOURISM_GALLERY, {}),  # Galleriat (galleries)
        357: (Categories.TOURISM_GALLERY, {}),  # Näyttelytilat (exhibition spaces)
        2262: (Categories.TOURISM_GALLERY, {}),  # Näyttelytilat (exhibition spaces)
        2006: (Categories.TOURISM_ARTWORK, {}),  # Veistokset ja julkinen taide (sculptures and public art)
        367: (Categories.TOURISM_ARTWORK, {}),  # Katutaidepaikat (street art spots)
        544: (Categories.MAN_MADE_PIER, {}),  # Kansainvälisten risteilyalusten laiturit (cruise piers)
        699: (Categories.TOURISM_INFORMATION, {}),  # Opastuspiste (info point)
        698: (Categories.TOURISM_VIEWPOINT, {}),  # Luontotorni (nature towers)
        2365: (Categories.TOURISM_INFORMATION, {}),  # Opastetaulut (signboards)
        2366: (Categories.TOURISM_INFORMATION, {}),  # Opastetaulut (signboards)
        34: (Categories.RECYCLING, {}),  # Keräyspisteet (collection points)
        52: (Categories.RECYCLING, {}),  # Kierrätyskeskus (recycling centre)
        2276: (Categories.SHOP_SECOND_HAND, {}),  # Kaikenkuntoisten sähkölaitteiden kierrättäminen (reuse shops)
        319: (Categories.OFFICE_GOVERNMENT, {}),  # Asiointipisteet, yleisneuvonta ja yhteispalvelu (service points)
        93: (Categories.OFFICE_GOVERNMENT, {}),  # Vesilaskut ja asiakaspalvelu (water billing and customer service)
        301: (Categories.OFFICE_GOVERNMENT, {}),  # Vesilaskut ja asiakaspalvelu (water billing and customer service)
        1379: (Categories.OFFICE_GOVERNMENT, {}),  # Perusopetuksen neuvonta (basic-education guidance)
        2136: (Categories.OFFICE_GOVERNMENT, {}),  # Perusopetuksen neuvonta (basic-education guidance)
        2004: (Categories.OFFICE_GOVERNMENT, {}),  # Hallinnolliset toimipisteet (administrative offices)
        1081: (Categories.OFFICE_GOVERNMENT, {}),  # Tullin asiointipisteet (customs service points)
        166: (Categories.OFFICE_GOVERNMENT, {}),  # Verotoimistot (tax offices)
        779: (Categories.OFFICE_GOVERNMENT, {}),  # Oikeusaputoimistot (legal-aid offices)
        782: (Categories.OFFICE_GOVERNMENT, {}),  # Ulosottovirastot (enforcement offices)
        179: (Categories.OFFICE_GOVERNMENT, {}),  # Kirjaamo (registries)
        2203: (Categories.OFFICE_GOVERNMENT, {}),  # Asiakaspalvelu (customer service)
        188: (Categories.OFFICE_GOVERNMENT, {}),  # Kelan etuudet (Kela benefits)
        239: (Categories.OFFICE_GOVERNMENT, {}),  # Kaupanvahvistus (property transaction confirmation)
        244: (Categories.OFFICE_GOVERNMENT, {}),  # Lainhuuto (title registration)
        2005: (Categories.OFFICE_GOVERNMENT, {}),  # Valtuustotalot (council buildings)
        321: (Categories.OFFICE_GOVERNMENT, {}),  # Johtotietopalvelu (cabling information service)
        322: (Categories.OFFICE_GOVERNMENT, {}),  # Karttapalvelut (mapping services)
        323: (Categories.OFFICE_GOVERNMENT, {}),  # Paikkatietoneuvonta (spatial-data guidance)
        168: (Categories.OFFICE_GOVERNMENT, {}),  # Alkavien yrittäjien neuvonta (startup advice)
        224: (Categories.OFFICE_GOVERNMENT, {}),  # Info- ja näyttelytilat (info and exhibition premises)
        315: (Categories.OFFICE_GOVERNMENT, {}),  # Info- ja näyttelytilat (info and exhibition premises)
        189: (Categories.OFFICE_GOVERNMENT, {}),  # Maahanmuuttajapalvelut (immigrant services)
        857: (Categories.OFFICE_GOVERNMENT, {}),  # Maahanmuuttajapalvelut (immigrant services)
        309: (Categories.ARCHIVE, {}),  # Kaupunginarkiston asiakaspalvelu (city archive service)
        132: (Categories.OFFICE_GOVERNMENT, {}),  # Kaupanvahvistus (property transaction confirmation)
        131: (Categories.OFFICE_GOVERNMENT, {}),  # Julkinen notaari (public notaries)
        133: (Categories.OFFICE_GOVERNMENT, {}),  # Kauppa- ja yhdistysrekisteri (trade registers)
        776: (Categories.OFFICE_GOVERNMENT, {}),  # Kotikunta- ja väestötiedot (residency records)
        777: (Categories.OFFICE_GOVERNMENT, {}),  # Kuluttajansuoja ja neuvonta (consumer advice)
        778: (Categories.OFFICE_GOVERNMENT, {}),  # Nimiasiat (name matters)
        771: (Categories.OFFICE_GOVERNMENT, {}),  # Avioehto (prenuptial agreements)
        2339: (Categories.OFFICE_GOVERNMENT, {}),  # Asumisneuvonta (housing advice)
        2187: (Categories.OFFICE_GOVERNMENT, {}),  # Vapaan sivistystyön neuvonta (adult-education guidance)
        2188: (Categories.OFFICE_GOVERNMENT, {}),  # Vapaan sivistystyön neuvonta (adult-education guidance)
        1362: (Categories.OFFICE_GOVERNMENT, {}),  # Asiakaspalvelu (customer service)
        1366: (Categories.OFFICE_GOVERNMENT, {}),  # Asiakaspalvelu (customer service)
        2379: (Categories.OFFICE_GOVERNMENT, {}),  # Työllisyyspalvelut (employment services)
        2202: (Categories.OFFICE_GOVERNMENT, {}),  # Syyttäjävirastot (prosecutor offices)
        820: (Categories.OFFICE_GOVERNMENT, {}),  # Iäkkäiden sosiaalityö (elderly social-work guidance desks)
        821: (Categories.OFFICE_GOVERNMENT, {}),  # Iäkkäiden sosiaaliohjaus (elderly social guidance)
        827: (Categories.SOCIAL_FACILITY, {}),  # Iäkkäiden omaishoidon tuki (elderly caregiver support)
        1069: (Categories.OFFICE_SECURITY, {}),  # Muut turvapalvelut (security services)
        2292: (Categories.SHOP_SHOE_REPAIR, {}),  # Suutarit (cobblers)
        217: (Categories.OFFICE_GOVERNMENT, {}),  # Sisäinen tarkastus (internal audit)
        279: (Categories.OFFICE_GOVERNMENT, {}),  # Rakennusvalvonta (building control)
        350: (Categories.PLACE_OF_WORSHIP, {}),  # Kirkot ja muut uskonnolliset tilat (churches)
        106: (Categories.VETERINARY, {}),  # Eläinlääkäripalvelut (vet services)
        724: (Categories.VETERINARY, {}),  # Luonnonvaraisten eläinten hoitola (wildlife care)
        23: (Categories.VETERINARY, {}),  # Luonnonvaraisten eläinten hoitola (wildlife care)
        753: (Categories.MARKETPLACE, {}),  # Torit (market squares)
        84: (Categories.MARKETPLACE, {}),  # Torit (market squares)
        83: (Categories.MARKETPLACE, {}),  # Markkinat (markets)
        81: (Categories.MARKETPLACE, {}),  # Kauppahallit (market halls)
        740: (Categories.MARKETPLACE, {}),  # Kauppahallit (market halls)
        2249: (Categories.SHOP_SECOND_HAND, {}),  # Käytettyjen tavaroiden myynti (second-hand sales)
        2293: (Categories.SHOP_TAILOR, {}),  # Ompelimot (tailor shops)
        2294: (Categories.CRAFT_UPHOLSTERER, {}),  # Verhoilijat (upholsterers)
        2295: (Categories.CRAFT_UPHOLSTERER, {}),  # Huonekalujen korjaus (furniture repair)
        2296: (Categories.SHOP_BICYCLE, {}),  # Pyörähuolto (bike repair)
        2300: (Categories.CRAFT_ELECTRONICS_REPAIR, {}),  # Muiden sähkölaitteiden korjaus (electronics repair)
        2299: (Categories.CRAFT_ELECTRONICS_REPAIR, {}),  # Kodinkonehuolto (appliance repair)
        2302: (Categories.CRAFT_WATCHMAKER, {}),  # Kellojen ja korujen korjaus (watch and jewellery repair)
        2298: (Categories.CRAFT_ELECTRONICS_REPAIR, {}),  # Puhelinhuolto (phone repair)
        2297: (Categories.CRAFT_ELECTRONICS_REPAIR, {}),  # Tietokonehuolto (computer repair)
        73: (Categories.ALLOTMENTS, {}),  # Viljelyspalstat (allotments)
        503: (Categories.ALLOTMENTS, {}),  # Viljelyspalstat (allotments)
        88: (Categories.SHOP_GARDEN_CENTRE, {}),  # Mullan myynti (bulk soil pickup retail)
        296: (Categories.SHOP_GARDEN_CENTRE, {}),  # Mullan myynti (bulk soil pickup retail)
        2377: (Categories.ALLOTMENTS, {}),  # Yhteisöviljelypaikat (community cultivation)
        2378: (Categories.ALLOTMENTS, {}),  # Yhteisöviljelypaikat (community cultivation)
        741: (Categories.SHOP_KIOSK, {}),  # Kioskit (kiosks)
        82: (Categories.SHOP_SECOND_HAND, {}),  # Kirpputorit (flea markets)
        2277: (
            Categories.SHOP_SECOND_HAND,
            {},
        ),  # Käyttökelpoisten tavaroiden ja tekstiilien kierrättäminen (reuse shops)
        2250: (Categories.SHOP_SECOND_HAND, {}),  # Uusiotuotteiden myynti (recycled-product sales)
        2190: (
            Categories.SHOP_HEALTH_FOOD,
            {},
        ),  # Terveys- ja hyvinvointikeskukset (health and wellness centres; filed units are health-food stores)
        396: (Categories.SHOP_SPORTS, {}),  # Jalkapallo (football; filed unit sells football goods)
        514: (Categories.SHOP_TICKET, {}),  # Asiakaspalvelu ja lipunmyynti (service and ticket sales, cf. HSL points)
        2268: (Categories.SHOP_RENTAL, {}),  # Vuokrauspalvelut (rental services, kiertotalous)
        2267: (Categories.SHOP_RENTAL, {}),  # Vertaisvuokrauspalvelut (peer-to-peer rentals)
        2269: (Categories.SHOP_RENTAL, {}),  # Muut lainaus- ja vuokrauspalvelut (borrowing and rentals)
        2266: (Categories.SHOP_RENTAL, {}),  # Vaatelainaamot (shared wardrobes)
        2305: (Categories.SHOP_SECOND_HAND, {}),  # Muut kiertotalouden palvelut (circular-economy services)
        727: (Categories.SHOP_GIFT, {}),  # Kauppa (store; the filed unit is a zoo souvenir shop, cf. unit 9349)
        176: (Categories.POST_OFFICE, {}),  # Postipalvelut (postal services)
        531: (Categories.PARKING, {}),  # Pysäköintitalot ja -tilat (parking garages)
        532: (Categories.PARKING, {}),  # Yleiset pysäköintialueet (public parking areas)
        2207: (Categories.PARKING, {}),  # Esteettömät autopaikat kadulla (accessible street parking)
        2204: (Categories.CAR_SHARING, {}),  # Yhteiskäyttöautojen pysäköintipaikat (shared-car parking)
        533: (Categories.CHARGING_STATION, {}),  # Sähköautojen latauspisteet (EV charging)
        530: (
            Categories.VENDING_MACHINE,
            {"vending": Vending.PARKING_TICKETS},
        ),  # Pysäköintilippuautomaatit (parking ticket machines)
        87: (Categories.WASTEWATER_PLANT, {}),  # Jäteveden puhdistamo (wastewater plant)
        295: (Categories.WASTEWATER_PLANT, {}),  # Jäteveden puhdistamo (wastewater plant)
        299: (Categories.WATER_WORKS, {}),  # Vedenpuhdistuslaitos (drinking-water plant)
        91: (Categories.WATER_WORKS, {}),  # Vedenpuhdistuslaitos (drinking-water plant)
        # Generic-coverage rows (2026-10): placed before the fallback so
        # they only win when no earlier tabled node matches. Each was
        # verified against all filed units before adding; see
        # tests/test_helsinki_servicemap_fi.py.
        2412: (Categories.TRAINING, {}),  # Nuorisosirkus (youth circus)
        2414: (Categories.TRAINING, {}),  # Perhesirkus (family circus)
        2416: (Categories.TRAINING, {}),  # Sirkuskoulu (circus schools)
        1369: (Categories.TRAINING, {}),  # Kuvataidekoulu (art schools)
        2401: (Categories.TRAINING, {}),  # Käsityökoulu (craft schools)
        2417: (Categories.MUSIC_SCHOOL, {}),  # Taidekoulu (art/music schools, cf. Sandels)
        2236: (Categories.LEISURE_PITCH, {"sport": Sport.CHESS}),  # Puistoshakkilaudat (park chessboards)
        2237: (Categories.LEISURE_PITCH, {"sport": Sport.CHESS}),  # Puistoshakkilaudat (park chessboards)
        18: (Categories.DOG_TOILET, {}),  # Koirakäymälät (dog toilets)
        64: (Categories.DOG_TOILET, {}),  # Koirakäymälät (dog toilets)
        495: (Categories.DOG_TOILET, {}),  # Koirakäymälät (dog toilets)
        600: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.ORIENTEERING}),  # Suunnistusalue (orienteering areas)
        2424: (Categories.LEISURE_PLAYGROUND, {}),  # Pulkkamäki (sledding hills)
        576: (Categories.LEISURE_SPORTS_CENTRE, {"sport": Sport.SKIING}),  # Laskettelun suorituspaikat (ski resorts)
        595: (
            Categories.LEISURE_SPORTS_CENTRE,
            {"sport": Sport.CROSS_COUNTRY_SKIING},
        ),  # Hiihtomaa (ski areas)
        596: (
            Categories.LEISURE_SPORTS_CENTRE,
            {"sport": Sport.CROSS_COUNTRY_SKIING},
        ),  # Kilpahiihtokeskus (cross-country ski centres)
        560: (Categories.LEISURE_PITCH, {"sport": Sport.SHOOTING}),  # Ampumarata (shooting ranges)
        628: (Categories.LEISURE_SPORTS_HALL, {"sport": Sport.SHOOTING}),  # Sisäampumarata (indoor ranges)
        593: (Categories.LEISURE_PITCH, {"sport": Sport.BIATHLON}),  # Ampumahiihdon harjoittelualue (biathlon areas)
        676: (Categories.AERODROME, {}),  # Urheiluilmailualue (sport airfields)
        275: (Categories.POWER_PLANT, {}),  # Voimalaitokset (power plants)
        27: (Categories.POWER_PLANT, {}),  # Voimalaitokset (power plants)
        2318: (Categories.SOCIAL_FACILITY_OUTREACH, {}),  # Perheneuvonta (family counselling teams)
        775: (Categories.OFFICE_GOVERNMENT, {}),  # Edunvalvonta (guardianship offices)
        135: (Categories.OFFICE_GOVERNMENT, {}),  # Kaupungin tai kunnan vuokra-asunnot (municipal housing offices)
        247: (Categories.OFFICE_GOVERNMENT, {}),  # Kaupungin tai kunnan vuokra-asunnot (municipal housing offices)
        249: (Categories.OFFICE_GOVERNMENT, {}),  # Asuntotonttien vuokraus ja myynti (plot allocation offices)
        137: (Categories.OFFICE_GOVERNMENT, {}),  # Asuntotonttien vuokraus ja myynti (plot allocation offices)
        225: (Categories.OFFICE_GOVERNMENT, {}),  # Kaavat ja kaavoitus (planning offices)
        227: (Categories.OFFICE_GOVERNMENT, {}),  # Liikennesuunnittelu (transport planning offices)
        2159: (Categories.OFFICE_GOVERNMENT, {}),  # Teknisten ja ympäristöpalvelujen neuvonta (advisory offices)
        104: (Categories.OFFICE_GOVERNMENT, {}),  # Asumisterveys (environmental health supervision)
        114: (Categories.OFFICE_GOVERNMENT, {}),  # Uimavesien valvonta (bathing-water supervision)
        998: (Categories.OFFICE_GOVERNMENT, {}),  # Tartuntaudit (disease surveillance back-offices)
        185: (Categories.OFFICE_EMPLOYMENT_AGENCY, {}),  # Rekrytointi (recruitment services)
        157: (Categories.OFFICE_PROPERTY_MANAGEMENT, {}),  # Liike- ja toimistotilojen vuokraus (commercial rentals)
        2021: (Categories.OFFICE_PROPERTY_MANAGEMENT, {}),  # Liike- ja toimistotilojen vuokraus (commercial rentals)
        274: (Categories.OFFICE_CONSULTING, {}),  # Energianeuvonta (energy advisory)
        313: (Categories.ARCHIVE, {}),  # Katu-, puisto- ja rakennuspiirustusten arkisto (planning archive)
        1039: (Categories.NUTRITIONIST, {}),  # Ravitsemusterapia (nutrition therapy)
        1037: (Categories.REHABILITATION, {}),  # Rintamavetaraanien kuntoutus (veterans' rehab)
        2386: (Categories.ASSISTED_LIVING, {}),  # Mielenterveyskuntoutujien perhehoito (family foster care)
        2385: (Categories.ASSISTED_LIVING, {}),  # Mielenterveyskuntoutujien perhehoito (family foster care)
        404: (Categories.COMMUNITY_CENTRE, {}),  # Kerhotoiminta (club rooms)
        355: (Categories.COMMUNITY_CENTRE, {}),  # Kulttuurin monitoimitalot (multicultural houses)
        548: (Categories.PLACE_ISLAND, {}),  # Ulkoilusaaret (excursion islands)
        704: (Categories.SHELTER, {}),  # Ulkoilumaja / hiihtomaja (outdoor huts)
        389: (Categories.COMMUNITY_CENTRE, {}),  # Fillari- ja moottoripaja (youth motor workshops)
        438: (Categories.COMMUNITY_CENTRE, {}),  # Moottorihalli (youth motor halls)
        440: (Categories.COMMUNITY_CENTRE, {}),  # Mopokerho (youth moped clubs)
        2425: (Categories.LEISURE_SPORTS_HALL, {}),  # Sisäaktiviteettipuisto (indoor activity parks)
        683: (Categories.LEISURE_SPORTS_CENTRE, {}),  # Vesihiihtoalue (water-ski areas)
        # Last on purpose: a generic fallback, so multi-node units keep
        # their real facility (cf. Tapanilan Urheilukeskus, Suomenlinnan
        # vierailijakeskus); single-node Gallträsk still resolves to park.
        711: (
            Categories.LEISURE_PARK,
            {},
        ),  # Monikäyttöalue, jolla on virkistyspalveluita (multi-use recreational areas)
    }

    operators_wikidata = {
        "Helsingin kaupunki": "Q1757",
        "Espoon kaupunki": "Q47034",
        "Vantaan kaupunki": "Q127623",
        "Kauniaisten kaupunki": "Q208287",
        "Helsingin yliopisto": "Q28695",
        "Aalto-korkeakoulusäätiö sr": "Q300980",
        "HUS-kuntayhtymä": "Q110737083",
        "Vantaan ja Keravan hyvinvointialue": "Q110245340",
        "Itä-Uudenmaan hyvinvointialue": "Q110245220",
        "Länsi-Uudenmaan hyvinvointialue": "Q110245203",
        "Kela": "Q3557354",
        "HSL": "Q473211",
        "Helsingin seudun ympäristöpalvelut HSY": "Q10520595",
        "Kirkkonummi": "Q748092",
        "Inkoo": "Q986331",
        "Siuntio": "Q984931",
        "Lohja": "Q214777",
        "Raasepori": "Q633371",
        "Vihti": "Q935858",
        "Suomen valtio": "Q33",
    }

    # No visitable service (housing, meal services, org records), linear
    # features (routes), road furniture (stops, crosswalks, hotspots),
    # back-office only (depots, planning). Snow dumps (78/538/75/535)
    # stay uncategorised: no established OSM tag.
    excluded_subtrees = {
        5,  # Asumisoikeusasuminen (right-of-occupancy housing)
        9,  # Kaupungin tai kunnan vuokra-asunnot (municipal rentals)
        10,  # Kaupungin tai kunnan työsuhdeasunnot (employer housing)
        11,  # Opiskelija-asunnot (student housing)
        12,  # Yksityiset vuokra-asunnot (private rentals)
        2354,  # Lyhytaikaisasunnot (short-term housing)
        2191,  # Hitas-asunnot (Hitas housing)
        2163,  # Päiväkotiruokailu (daycare kitchens)
        1376,  # Koulu- ja opiskelijaruokailu (school meal services)
        861,  # Hoitoalan ruokapalvelut (care-sector meal services)
        504,  # Ruoka- ja cateringpalvelut (food and catering services)
        71,  # Viheralueet (green areas)
        502,  # Viheralueet (green areas)
        399,  # Järjestötoiminta (org-activity records)
        768,  # Järjestötoiminta (org-activity records)
        2205,  # Ääniopastetut suojatiet (audio-guided crosswalks)
        2206,  # Ääniopastetut suojatiet (audio-guided crosswalks)
        331,  # WLAN-sisäpisteet (wifi hotspots)
        582,  # Kävelyreitti (walking routes)
        583,  # Latu (ski tracks)
        584,  # Luontopolku (nature trails)
        585,  # Maastopyöräilyreitti (mountain-bike routes)
        581,  # Kuntorata (fitness tracks)
        580,  # Koirahiihtolatu (dog ski tracks)
        591,  # Vesiretkeilyreitti (paddling routes)
        590,  # Retkeilyreitti (hiking routes)
        589,  # Pyöräilyreitti (cycling routes)
        586,  # Melontareitti (canoeing routes)
        579,  # Hevosreitti (riding routes)
        2429,  # Rullahiihtorata (roller-ski tracks)
        643,  # Luistelureitti (skating routes)
        515,  # Joukkoliikennepysäkit (public-transport stops; bus service, no single premises)
        2444,  # Huoltorakennukset (maintenance buildings)
        1033,  # Kuntoutussuunnittelu ja -ohjaus (rehab planning)
        516,  # Julkisen liikenteen varikot (transit depots)
        77,  # Katujen ja viheralueiden suunnittelu ja rakennuttaminen (street planning)
        277,  # Katujen ja viheralueiden suunnittelu ja rakennuttaminen (street planning)
        537,  # Katujen ja viheralueiden suunnittelu ja rakennuttaminen (street planning)
    }

    # ---- Crawl plumbing: bootstrap departments, build the service-node
    # ---- graph, page units with dedupe and count-drift accounting.
    async def start(self):
        self.rule_precedence = {node_id: i for i, node_id in enumerate(self.SERVICE_NODES)}
        self.departments = {}
        self.all_service_nodes = set()
        self.parent_service_node = {}
        self.rule_by_service_node = {}
        self.seen_next = set()
        self.seen_places = set()
        self.expected_units = None
        self.seen_units = 0
        self.units_pages_pending = 0
        # Departments and the node tree are independent: fetch both at once
        # (one round trip saved matters under CI's 120s kill) and start the
        # units only after both paginations finish.
        self.bootstrap_pending = {"departments", "service_nodes"}
        yield JsonRequest(
            url=f"{self.api_base_url}/department/?page_size={self.page_size}&format=json",
            callback=self.parse_departments,
            errback=self.parse_bootstrap_error,
        )
        yield JsonRequest(
            url=f"{self.api_base_url}/service_node/?page_size={self.page_size}&format=json",
            callback=self.parse_service_nodes,
            errback=self.parse_bootstrap_error,
        )

    def _bootstrap_done(self, key):
        # One bootstrap leg finished paging; returns the first units request
        # once both legs are done, else None.
        self.bootstrap_pending.discard(key)
        if self.bootstrap_pending:
            return None
        self._build_service_graph()
        return JsonRequest(
            url=f"{self.api_base_url}/unit/?page_size={self.page_size}&format=json",
            callback=self.parse_units,
            errback=self.parse_unit_page_error,
        )

    def _stat(self, suffix, n=1):
        self.crawler.stats.inc_value(f"atp/{self.name}/{suffix}", n)

    def parse_bootstrap_error(self, failure):
        self._stat("page/failed")
        request = failure.request
        status = getattr(getattr(failure.value, "response", None), "status", None)
        raise CloseSpider(f"bootstrap {request.url} failed ({status or type(failure.value).__name__})")

    def _retry_units(self, request):
        return JsonRequest(
            url=request.url,
            callback=self.parse_units,
            errback=self.parse_unit_page_error,
            meta={**request.meta, "retried": True},
        )

    def parse_unit_page_error(self, failure):
        self._stat("page/failed")
        self.logger.error("unit page failed: %s", failure.request.url)
        if failure.request.meta.get("retried"):
            self._stat("page/skipped")
            self._count_page_done(failure.request)
            return None
        yield self._retry_units(failure.request)

    def _payload(self, response):
        content_type = (response.headers.get("Content-Type") or b"").decode().lower()
        if "json" not in content_type:
            raise CloseSpider(f"expected JSON, got {content_type!r} for {response.url}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise CloseSpider(f"bad JSON from {response.url}: {exc}") from exc
        if not isinstance(payload, dict):
            # Error bodies must fail loudly, never parse as an empty result set.
            raise CloseSpider(f"expected JSON object from {response.url}")
        return payload

    def _walk(self, node_id):
        seen = set()
        current = node_id
        # Malformed data can point a node at its own ancestor.
        while current is not None and current not in seen:
            seen.add(current)
            yield current
            current = self.parent_service_node.get(current)

    def _follow(self, payload, callback, errback):
        next_url = payload.get("next")
        if not next_url:
            return None
        # Keyed per pagination leg: identical next-URL shapes across the
        # department/node/unit legs must never false-positive a loop.
        key = (getattr(callback, "__name__", None), next_url)
        if key in self.seen_next:
            raise CloseSpider(f"pagination loop at {next_url}")
        self.seen_next.add(key)
        return JsonRequest(url=next_url, callback=callback, errback=errback)

    def parse_departments(self, response):
        payload = self._payload(response)
        for department in payload.get("results") or []:
            if not isinstance(department, dict):
                # One malformed row must not kill the whole page.
                continue
            dept_name = department.get("name")
            # Non-dict names must not kill the page (cf. str-valued name).
            name = dept_name.get("fi") if isinstance(dept_name, dict) else None
            if type(department.get("id")) is int and name:
                self.departments[department["id"]] = name.strip()
        if request := self._follow(payload, self.parse_departments, self.parse_bootstrap_error):
            yield request
            return
        if request := self._bootstrap_done("departments"):
            yield request

    def parse_service_nodes(self, response):
        payload = self._payload(response)
        for node in payload.get("results") or []:
            if not isinstance(node, dict):
                continue
            # ids/parents must be real ints: unhashable or bool values would
            # poison the service graph walk (cf. True == 1).
            if type(node.get("id")) is not int:
                continue
            self.all_service_nodes.add(node["id"])
            if type(node.get("parent")) is int:
                self.parent_service_node[node["id"]] = node["parent"]
        if request := self._follow(payload, self.parse_service_nodes, self.parse_bootstrap_error):
            yield request
            return
        if request := self._bootstrap_done("service_nodes"):
            yield request

    def _build_service_graph(self):
        self.rule_by_service_node = {}
        for node_id in self.parent_service_node:
            matches = [a for a in self._walk(node_id) if a in self.SERVICE_NODES]
            if matches:
                self.rule_by_service_node[node_id] = self._earliest(matches)
        for root in self.SERVICE_NODES:
            self.rule_by_service_node.setdefault(root, root)
        missing = [node_id for node_id in self.SERVICE_NODES if node_id not in self.all_service_nodes]
        stale = [node_id for node_id in self.excluded_subtrees if node_id not in self.all_service_nodes]
        for ids, label in ((missing, "tabled"), (stale, "excluded")):
            if ids:
                self.logger.warning("%s service nodes missing from tree: %s", label, ids)
                self._stat(f"{label}/missing", len(ids))

    # Dedupe keys: name, coords, every category tag, located_in. The offline
    # harness reuses this tuple; _has_category reads it too. historic rides
    # along for memorials (no mappable top-level tag otherwise).
    DEDUPE_TAGS = (
        "shop",
        "amenity",
        "leisure",
        "tourism",
        "office",
        "healthcare",
        "social_facility",
        "craft",
        "man_made",
        "military",
        "mooring",
        "place",
        "natural",
        "emergency",
        "building",
        "railway",
        "sport",
        "landuse",
        "historic",
        "aeroway",
        "power",
    )

    def parse_units(self, response):
        try:
            payload = self._payload(response)
        except CloseSpider:
            if response.request.meta.get("retried"):
                raise
            self._stat("page/failed")
            self.logger.error("unit page unreadable, retrying: %s", response.request.url)
            yield self._retry_units(response.request)
            return
        if self.expected_units is None:
            # Coerced once: a string count must not poison the int drift
            # comparison below (int != str warns forever).
            count = payload.get("count")
            self.expected_units = count if type(count) is int else None
        for unit in payload.get("results") or []:
            try:
                item = self._build_item(unit)
            except Exception:
                self._stat("item/failed")
                self.logger.exception("bad unit: %r", unit.get("id") if isinstance(unit, dict) else unit)
                continue
            if item is not None:
                # Pipeline dedupes on ref only; collapse same name/coords/category
                # here (categories live in extras, hence get_tag). Branch rides
                # along since chain sites share names (cf. Aimo Park halls).
                key = (
                    item.get("name"),
                    round(float(item.get("lon")), 7),
                    round(float(item.get("lat")), 7),
                    *(item.get_tag(tag) for tag in self.DEDUPE_TAGS),
                    item.get("located_in"),
                    item.get("branch"),
                )
                if key in self.seen_places:
                    self._stat("dropped/duplicate")
                    continue
                self.seen_places.add(key)
                self.seen_units += 1
                self._stat("item/yielded")
                yield item
        if response.request.meta.get("paged"):
            pass  # Fanned page: results already scheduled, no chaining.
        elif request := self._fan_unit_pages(response.request, payload):
            yield from request
        elif request := self._follow(payload, self.parse_units, self.parse_unit_page_error):
            yield request
            self._count_page_done(response.request)
            return
        self._count_page_done(response.request)
        if self.units_pages_pending <= 0:
            # Chain end (sequential) or drained fan: the only point where
            # seen-vs-expected is meaningful. Mid-chain pages always
            # "drift", so checking there is pure log spam.
            self._check_unit_drift()

    def _count_page_done(self, request):
        if self.units_pages_pending > 0 and not request.meta.get("counted"):
            request.meta["counted"] = True
            self.units_pages_pending -= 1

    def _fan_unit_pages(self, request, payload):
        # First unit page carries the row count: fetch the rest up front
        # instead of next-chaining 22 pages (~90s) into CI's 120s kill.
        # Falls back to sequential when the count is missing.
        if request.meta.get("paged"):
            return None
        count = payload.get("count")
        if not isinstance(count, int) or count <= 0:
            return None
        total = max(1, -(-count // self.page_size))
        self.units_pages_pending = total
        requests = []
        for page in range(1, total + 1):
            if page == 1:
                continue
            requests.append(
                JsonRequest(
                    url=f"{self.api_base_url}/unit/?page={page}&page_size={self.page_size}&format=json",
                    callback=self.parse_units,
                    errback=self.parse_unit_page_error,
                    meta={"paged": True},
                )
            )
        return requests

    def _check_unit_drift(self):
        if self.expected_units is None:
            return
        dropped = sum(
            self.crawler.stats.get_value(f"atp/{self.name}/dropped/{reason}", 0)
            for reason in (
                "not_displayed",
                "non_place",
                "no_coords",
                "invalid",
                "no_name",
                "test_data",
                "duplicate",
            )
        ) + self.crawler.stats.get_value(f"atp/{self.name}/item/failed", 0)
        +self.crawler.stats.get_value(f"atp/{self.name}/page/skipped", 0)
        if self.seen_units + dropped != self.expected_units:
            self.logger.warning(
                "unit count drift: api=%s seen=%s dropped=%s",
                self.expected_units,
                self.seen_units,
                dropped,
            )

    def _service_ids(self, unit):
        def _one(value):
            # type() is int, not isinstance: bool is int and True == 1
            # would file junk booleans under node 1.
            if type(value) is int:
                return value
            if isinstance(value, str) and value.isdigit():
                return int(value)
            return None

        service_ids = unit.get("service_nodes") or []
        if not isinstance(service_ids, list):
            return [_one(service_ids)] if _one(service_ids) is not None else []
        return [node_id for value in service_ids if (node_id := _one(value)) is not None]

    # ---- Item assembly: record filters, then one _apply_* per concern.
    def _is_test_unit(self, unit):
        # The production feed carries its own test records
        # ("Testi alaorganisaatio", "Henna testaa 2").
        name = unit.get("name")
        if not isinstance(name, dict):
            return False
        blob = " ".join(str(name.get(lang) or "") for lang in ("fi", "sv", "en")).lower()
        if "test" not in blob:
            # Every test morpheme below contains "test"; skip the token loop.
            return False
        return any(
            # Finnish test morphemes, not substrings: "protesti"/"testimonial"/
            # "attest"/"hottest" must not match, but "Esteettömyystestipiste" must.
            token == "test"
            or token.startswith(("testaa", "testaus"))
            or (
                token.startswith("testi")
                and not token.startswith(("testimonial", "testimony", "testament", "testing", "tested"))
            )
            or (
                token.endswith(("testi", "testaus", "testipiste", "testauspiste"))
                and not token.startswith(
                    ("protest", "contest", "latest", "greatest", "attest", "detest", "hottest", "cutest")
                )
            )
            or ("testi" in token and "piste" in token and not token.startswith(("protest", "contest", "attest")))
            for token in re.split(r"\W+", blob)
        )

    def _parse_lonlat(self, coordinates):
        try:
            lon, lat = float(coordinates[0]), float(coordinates[1])
        except (IndexError, KeyError, TypeError, ValueError):
            return None
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return None
        # Service-map data is Finnish: a swapped pair (lat 24.9, lon 60.1)
        # passes the global range yet lands in Yemen. Åland (~19.5E) included.
        if not (59.0 <= lat <= 71.0 and 19.0 <= lon <= 32.0):
            return None
        return lon, lat

    def _build_item(self, unit):
        if not isinstance(unit, dict) or unit.get("id") is None:
            self._stat("dropped/invalid")
            return None
        contract = unit.get("contract_type") or {}
        if contract == "NOT_DISPLAYED" or (isinstance(contract, dict) and contract.get("id") == "NOT_DISPLAYED"):
            self._stat("dropped/not_displayed")
            return None
        if self._is_test_unit(unit):
            self._stat("dropped/test_data")
            return None
        service_ids = self._service_ids(unit)
        if service_ids and all(
            any(ancestor in self.excluded_subtrees for ancestor in self._walk(service_id)) for service_id in service_ids
        ):
            self._stat("dropped/non_place")
            return None

        location = unit.get("location") or {}
        if not isinstance(location, dict):
            self._stat("dropped/invalid")
            return None
        coordinates = location.get("coordinates") or []
        if not isinstance(coordinates, (list, tuple)):
            self._stat("dropped/no_coords")
            return None
        parsed = self._parse_lonlat(coordinates)
        if parsed is None:
            self._stat("dropped/no_coords")
            return None
        lon, lat = parsed

        item = Feature()
        item["ref"] = str(unit["id"])
        # ATP ref is the spider-scoped record key, not an OSM ref tag.
        # Keep the ServiceMap id namespaced for imports (cf. ref:msal).
        item["extras"]["ref:palvelukartta"] = str(unit["id"])
        item["lon"], item["lat"] = lon, lat

        self._apply_name(item, unit)
        if not item.get("name"):
            # No name in any language: not a mappable POI.
            self._stat("dropped/no_name")
            return None
        # Category before operator and parking: both read the applied tags.
        self._apply_address(item, unit)
        self._apply_category(item, unit)
        self._apply_operator(item, unit)
        self._apply_brand(item, unit)
        self._apply_contact(item, unit)
        self._apply_media(item, unit)
        self._apply_lipas_extras(item, unit)
        self._apply_end_date(item, unit)
        return item

    def _apply_end_date(self, item, unit):
        # Announced closures live in names: "..., toiminta päättyy 30.6.2026".
        name = unit.get("name") or {}
        if not isinstance(name, dict):
            return
        match = re.search(r"toiminta päättyy (\d{1,2})\.(\d{1,2})\.(\d{4})", str(name.get("fi") or "").lower())
        if not match:
            return
        try:
            end = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1))).date()
        except ValueError:
            return
        item["extras"]["end_date"] = end.isoformat()

    # ---- Name handling: facility/venue splits, provider-tail cleaning,
    # ---- closure notes, official designations, translations.
    # Activity/type words, never venues; zero-width chars are feed noise.
    ZW_CHARS = re.compile("[\u200b-\u200d\ufeff]")
    NO_SPLIT_VENUES = (
        "iltapäivätoiminta",
        "eftermiddagsverksamhet",
        "finskspråkig eftermiddagsverksamhet",
        "after-school activities",
        "after-school activites",
        "ekopiste",
        "ekopunkt",
        "kierrätyspiste",
    )

    # Records whose nodes are all student-welfare services: a school name
    # is the venue, not the POI (cf. Koivukylän koulu).
    WELFARE_NODES = frozenset({1374, 1375, 2350, 2164, 2165, 2166, 2167})

    # Tails that are institutions are venues, not facilities: the service
    # comes first ("Kalasan toimintaterapia/Malmin sairaala").
    INSTITUTION_TAILS = (
        "sairaala",
        "terveysasema",
        "neuvola",
        "asema",
        "kirkko",
        "kappeli",
        "kirjasto",
        "uimahalli",
        "museo",
        "teatteri",
        "koulu",
        "lukio",
        "opisto",
        "päiväkoti",
        "skola",
        "skolan",
        "gymnasium",
        "daghem",
        "virasto",
        "satama",
        "tori",
        "talo",
        "keskus",
        "toimisto",
        "laitos",
    )

    # Combined institutions ("Karkkilan yläaste/lukio", "A yläaste / lukio"),
    # not venue/facility splits.
    SCHOOL_TAIL_RE = re.compile(
        r"(yläaste|ala-aste|peruskoulu|yhtenäiskoulu|lukio|koulu|opisto|päiväkoti|skola|skolan|daghem\w*|förskol\w*|gymnasi\w*)\s*$"
    )

    VENUE_WORDS_RE = re.compile(
        r"(\w*(päiväkoti|lukio|opisto|koulu)\b|\b(skola|skolan|daghem\w*|förskol\w*|gymnasi\w*|omnia|preschool|playschool|nursery|montessori|kindergarten|school)\b)"
    )

    # School words anywhere in a comma head ("Kallion ala-aste");
    # VENUE_WORDS_RE misses ala-aste/yläaste/peruskoulu forms. Only used
    # with service tails, so the broad match cannot misfire elsewhere.
    SCHOOL_HEAD_RE = re.compile(
        r"(ala-aste|yläaste|yläkoulu|peruskoulu|yhtenäiskoulu|lyseo|lukio|koulu|opisto|päiväkoti|skola|skolan|gymnasi\w*|daghem\w*)"
    )

    # Institution tails are venues ("Malmin sairaala"); end-anchored so
    # lookalikes like "auditorio" never match. Compounds match too
    # ("perhekeskus" via keskus). Built from the tuple above.
    INSTITUTION_TAIL_RE = re.compile(r"\w*(?:" + "|".join(re.escape(w) for w in INSTITUTION_TAILS) + ")$")

    # Surnames that end in institution-tail words must never invert a
    # slash split ("Palvelu / Eskola" names the room Eskola, cf. unit 77092
    # shape). End-anchoring alone cannot tell Eskola from perhekeskus.
    NO_INVERT_FACILITIES = frozenset({"eskola"})

    # Mall names anchored to the start, or suffixed without a comma.
    MALL_START_RE = re.compile(r"^(kauppakeskus|lippulaiva|iso omena|mall\b|ostari|ostoskeskus)\b")
    MALL_ANY_RE = re.compile(r"\b(ostari|ostoskeskus)\b")

    UFF_RE = re.compile(r"\buff\b")
    PAR3_RE = re.compile(r"\bpar[\s-]?3\b")

    @staticmethod
    def _mask_parens(text):
        # Blank parenthetical spans (same length) so slash splitting
        # ignores slashes inside them ("Uimastadion kuntorata /
        # Ulkokuntosali (Pohjoinen Stadiontie / Muistomerkki)", unit
        # 42121, splits at the facility slash, not the parenthetical).
        chars = list(text)
        depth = 0
        for i, ch in enumerate(chars):
            if ch == "(":
                depth += 1
                chars[i] = " "
            elif ch == ")":
                chars[i] = " "
                if depth:
                    depth -= 1
            elif depth:
                chars[i] = " "
        return "".join(chars)

    def _split_facility(self, text):
        # "Vesalan liikuntapuisto / Pienpelikenttä 2" -> facility in venue.
        # Bare slashes too ("Puolarmaarin ulkoilukeskus/koripallokenttä"),
        # but compounds without spaces stay whole (koripallo/lentopallo).
        text = re.sub(self.ZW_CHARS, "", str(text)).strip()
        masked = self._mask_parens(text)
        if " / " in masked:
            idx = masked.rfind(" / ")
            venue, facility = text[:idx], text[idx + 3 :]
        elif "/" in masked:
            idx = masked.rfind("/")
            venue, facility = text[:idx], text[idx + 1 :]
            if " " not in venue.strip() and " " not in facility.strip():
                return text, None
            if re.fullmatch(r"[a-zåäö]+", facility.strip()) and not facility.strip().endswith(
                (
                    "kenttä",
                    "sali",
                    "rata",
                    "maja",
                    "kota",
                    "katos",
                    "allas",
                    "talo",
                    "keskus",
                    "halli",
                    "puisto",
                    "paikka",
                    "alue",
                    "tori",
                    "toimisto",
                    "stadion",
                    "areena",
                )
            ):
                # Spaceless qualifier, not a facility ("Nuorten vastaanotto
                # Kallio/vaativa", unit 68047): keep the whole name rather
                # than naming the unit after debris. Lowercase-only on
                # purpose: capitalized single words (".../Aallotar") are
                # real facility names and must still split.
                return text, None
        else:
            return text, None
        ven, fac = venue.strip(), facility.strip()
        if fac.lower() in ("nurmi", "hiekka", "tekonurmi", "sora", "asfaltti", "gräs", "grass") and (
            " / " in ven or "/" in ven
        ):
            # Surface as last segment ("Myllypuron liikuntapuisto /
            # Baseball-kenttä / nurmi", unit 60097): the middle names the
            # facility, the first the venue.
            ven, _, fac = ven.rpartition("/") if " / " not in ven else ven.rpartition(" / ")
            ven, fac = ven.strip(), fac.strip()
        if len(ven) <= 1 or len(fac) <= 1:
            # Ship prefixes ("M/S Carmel Terrace", unit 77887): single
            # letters are never a venue or a facility.
            return text, None
        ven_l, fac_l = ven.lower(), fac.lower()
        head0 = venue.split("/")[0].strip().casefold()
        if head0 in self.NO_SPLIT_VENUES:
            # Activity-headed chains ("Iltapäivätoiminta / Toivolan koulu / ...",
            # "Ekopiste/A/B").
            return text, None
        if re.search(self.SCHOOL_TAIL_RE, fac_l) and re.search(self.SCHOOL_TAIL_RE, ven_l):
            # Combined institutions ("Karkkilan yläaste/lukio", "A yläaste / lukio"):
            # both sides name school levels. A service at a school
            # ("opiskeluhuolto / Malmin koulu") splits below instead.
            return text, None
        memorial = ("muistomerk", "monument", "minnesmärk", "memorial")
        if (
            any(word in fac_l for word in memorial)
            and not any(word in ven_l for word in memorial)
            and "(" not in text
            and ")" not in text
        ):
            # Memorial dedications name the artwork, not a venue ("Lähde /
            # UKK-monumentti", unit 23246, is the Lähde memorial to
            # president Kekkonen): the title side is the name, no venue.
            return ven, None
        if fac_l == "sosiaalitoimisto":
            # Service desks, not venues ("Karkkilan kaupungintalo/
            # sosiaalitoimisto", unit 71716): the service is the name,
            # the building the venue.
            return fac, ven
        if fac_l not in self.NO_INVERT_FACILITIES and re.search(self.INSTITUTION_TAIL_RE, fac_l):
            # Tails that are institutions are venues ("Malmin sairaala",
            # "Vuosaaren perhekeskus", compounds included); end-anchored so
            # lookalikes like "auditorio" never match ("tori" is not at end).
            return ven, fac
        if any(
            word in ven_l for word in ("opiskeluhuolto", "esiopetus", "kouluterveydenhuolto", "opiskeluterveydenhuolto")
        ) and re.search(self.VENUE_WORDS_RE, fac_l):
            # Service-headed slash pairs read like the comma form
            # ("Esiopetuksen opiskeluhuolto / Playschool Espoonlahti"):
            # the service comes first, the school is the venue.
            return ven, fac
        if "toimintaterapia" in ven_l and "terapia" not in fac_l:
            # Therapy at a named site ("Lasten toimintaterapia/Länsi-Pasila",
            # unit 69066): the service is the name. Sub-units naming their
            # own therapy (unit 69061) keep the default split.
            return ven, fac
        if re.search(self.COMMA_STREET_RE, ven_l):
            # Bare street addresses are parsed into street/housenumber, never
            # located_in ("Kurkisuontie 2 / Hiekkakenttä", unit 45330).
            return fac, None
        return fac, ven

    def _clean_name(self, raw):
        # Closure notes are metadata (end_date carries them), as are
        # trailing provider names ("Myyrmäen asukastila, Sporttia kaikille ry").
        # Bare organisation names ("Allergia-, Iho- ja Astmaliitto ry") stay whole.
        primary = re.sub(r",\s*toiminta päättyy.*$", "", raw, flags=re.IGNORECASE).strip()
        primary = re.sub(r",\s*SULJETTU TOISTAISEKSI\s*$", "", primary, flags=re.IGNORECASE).strip()
        # Register flags, never name parts ("Daghemmet Fyndet Kanel,
        # yksityinen", unit 64929, in all three languages).
        primary = re.sub(r",\s*(yksityinen|yksityiset|privat|private)\.?$", "", primary, flags=re.IGNORECASE).strip()
        # Bureau tails are record metadata ("Iltapäivätoiminta / ... /
        # Vaativan tuen erityisopetus, Kasvatuksen ja koulutuksen toimiala
        # (...)", unit 79871).
        primary = re.sub(r",\s*Kasvatuksen ja koulutuksen toimiala.*$", "", primary).strip()
        primary = re.sub(r",\s*Sektorn för fostran och utbildning.*$", "", primary).strip()
        primary = re.sub(r",\s*Education Division$", "", primary).strip()
        primary = re.sub(r",\s*valaistu\s*$", "", primary, flags=re.IGNORECASE).strip()
        # Raw coordinates leaked into island names ("Kuusiluoto, P 60°
        # 12,239' ja I 24° 59,696'", unit 57204; "Lähteelän ulkoilualue N
        # 59° 58,8' E 24° 26,3'", unit 57612): cut at the first degree mark.
        primary = re.sub(r"\s*(?:[PN]\s*)?\d+\s*°.*$", "", primary).strip(" ,-/–").strip()
        if not primary:
            primary = raw.strip()
        org_stripped = re.sub(r"[,/]\s*[^,/]*\b(r\.y\.|ry|oy|ab)\.?$", "", primary, flags=re.IGNORECASE).strip()
        if (
            org_stripped
            and org_stripped != primary
            and (
                " / " in org_stripped
                or re.search(
                    r"(päiväkoti|lukio|opisto|koulu|kirjasto|museo|kirkko|teatteri|uimahalli|satama|skola|iltapäivätoiminta|eftermiddagsverksamhet|after-school activit|fter-school activit|asukastila)\b",
                    org_stripped.lower(),
                )
            )
        ):
            primary = org_stripped
        return primary

    def _apply_machine_name(self, item, name):
        # Ticket machines are systematic identifiers, not venue names:
        # "Pysäköintilippuautomaatti 591, Eläintarhantie / 1, korttimaksu".
        # Quoted identifiers carry spaces ("Koivukylä 1"), so match them whole.
        fi = re.sub(self.ZW_CHARS, "", str(name.get("fi") or "")).strip()
        match = re.match(r'^Pysäköintilippuautomaatti\s+("[^"]+"|\S+)', fi)
        if not match:
            return False
        item["name"] = "Pysäköintilippuautomaatti " + match.group(1).rstrip(",")
        if item["name"] != fi:
            item["extras"]["official_name"] = fi
        low = fi.lower()
        if "korttimaksu" in low:
            item["extras"]["payment:credit_cards"] = "yes"
            item["extras"]["payment:debit_cards"] = "yes"
        if "kolikkomaksu" in low:
            item["extras"]["payment:coins"] = "yes"
        sv = str(name.get("sv") or "").strip()
        sv_match = re.match(r'^Parkering[s]?biljettautomat\s+("[^"]+"|\S+)', sv)
        if sv_match:
            sv_name = "Parkeringsbiljettautomat " + sv_match.group(1).rstrip(",")
            if sv_name != item["name"]:
                item["extras"]["name:sv"] = sv_name
        elif sv and sv != item["name"]:
            item["extras"]["name:sv"] = sv
        return True

    # Comma tails that are street addresses ("Mäkelänkatu 84",
    # "Malmgatan 20-21"): same suffix set as STREET_SUFFIXES, hoisted so
    # the pattern compiles once instead of per comma name.
    COMMA_STREET_RE = re.compile(
        r"(tie|katu|kuja|polku|väylä|raitti|ranta|kaari|esplanadi|bulevardi|vägen|väg|gatan|gata|gränden|gränd|stigen|stig)\s+\d"
    )

    # Court/field/hall tails that name the facility, not the venue
    # (lentopallokenttä, liikuntasali); per-language like the other
    # end-anchored rules. Bare kenttä/sali excluded: "Mäntymäen kenttä"
    # names the field itself.
    FACILITY_TAIL_RE = re.compile(
        r"(\w*(pallo|koris|tennis|sulkapallo|salibandy|hiekka|nurmi|tekonurmi)kenttä"
        r"|\w*(liikunta|urheilu|palloilu)sali"
        r"|\w*(bollplan|basketplan|fotbollsplan|tennisplan|friidrottsplan)"
        r"|\w*(idrottshall|sporthall)"
        r"|(football|volleyball|basketball|tennis|ball|playground)\s+(field|court)"
        r"|sports?\s+hall)$"
    )

    # Provider chains embedded as infixes ("Aalto-yliopisto Terveystalo
    # Otaniemi", unit 50608): host provider site. Word-mode only, like UFF.
    PROVIDER_INFIX = {"terveystalo": ("Terveystalo", "Q11897034")}

    def _split_provider_infix(self, text):
        for keyword, (brand, _qid) in self.PROVIDER_INFIX.items():
            match = re.search(r"\b" + re.escape(keyword) + r"\b", text, flags=re.IGNORECASE)
            if match and text[: match.start()].strip() and text[match.end() :].strip():
                head, tail = text[: match.start()].strip(), text[match.end() :].strip()
                return f"{brand} {tail}", head
        return None, None

    def _provider_infix_identity(self, text):
        for keyword, (brand, qid) in self.PROVIDER_INFIX.items():
            if re.search(r"\b" + re.escape(keyword) + r"\b", text, flags=re.IGNORECASE):
                return brand, qid
        return None

    def _split_comma_venue(self, primary):
        # Service at a preschool group; bare "X esiopetus" too, unless the
        # head names the venue ("Tuohimäen päiväkoti, esiopetus" stays whole).
        head, _, tail = primary.rpartition(",")
        if head.strip() and self.COMMA_STREET_RE.search(tail.strip().lower()):
            # Address tail ("Koskelan ala-asteen koulu, Mäkelänkatu 84",
            # "Alueellinen keräyspiste, Malmgatan 20-21").
            return head.strip(), None
        svc, _, rest = primary.partition(",")
        if svc.strip() and re.search(
            r"(kouluterveydenhuolto|opiskeluterveydenhuolto|opiskeluhuolto|elevhälsa|skolhälsovård|student welfare|school health care)$",
            svc.strip().lower(),
        ):
            # Service-first health names ("Esiopetuksen opiskeluhuolto,
            # Touhula Fallåker", unit 78143; "Opiskeluhuolto, Karhusuon
            # koulu", unit 69678): the service is the name, the rest the
            # venue. First comma, so middle segments stay with the venue
            # ("Opiskeluhuolto, Karjaan yhteiskoulu, lukio", unit 69833);
            # lowercase tails are descriptions, not places ("...,
            # keskitetty palvelu Espoo ja Kauniainen", unit 69236).
            if rest.strip() and rest.strip()[0].isupper():
                return svc.strip(), rest.strip()
            return primary, None
        if head.strip() and "ankkalampi" in head.strip().lower():
            # Private-chain daycares name the site after the comma
            # ("Päiväkoti Ankkalampi, Punavuori", unit 29918; "Päiväkoti
            # Ankkalampi,Töölö - Duckies", unit 33747, missing space
            # included): the site is the venue. Self-referential tails
            # ("...Mechelininkadun Ankkalampi-Ankdammen", unit 46377)
            # stay whole.
            tail_clean = tail.strip()
            if tail_clean and "ankkalampi" not in tail_clean.lower():
                return head.strip(), tail_clean
        if head.strip() and re.search(self.FACILITY_TAIL_RE, tail.strip().lower()):
            # Facility tails read like the slash form ("Puistokenttä
            # Linnaistenmetsä, lentopallokenttä", unit 57400, cf. the
            # slash twins that already split): the court is the name.
            return tail.strip(), head.strip()
        if head.strip() and (
            match := re.match(r"(.+?)\s+-\s+(?:\w+\s+)*kielikylpy\w*$", tail.strip(), flags=re.IGNORECASE)
        ):
            # Branch descriptors, not venues ("Tapiola - ruotsin kielen
            # kielikylpypäiväkoti", unit 20243): the district locates it.
            return head.strip(), match.group(1).strip()
        if head.strip() and re.search(r"(toimipaikka|opetuspiste|toimipiste)$", tail.strip().lower()):
            # Hosted sites ("Vantaan musiikkiopisto, Aurinkokiven koulun
            # opetuspiste", unit 68526; "Työtehoseura, Sarkatien
            # toimipiste", unit 69937): the institution is the name, the
            # site the venue.
            return head.strip(), tail.strip()
        if head.strip().lower() in ("shakkilauta", "shakkilaudat"):
            # Street-furniture chessboards at named places ("Shakkilauta,
            # Tilkantori", unit 63009; parks to squares, 25 units): the
            # place is the venue.
            if tail.strip() and not self.COMMA_STREET_RE.search(tail.strip().lower()):
                return head.strip(), tail.strip()
        if head.strip().lower() == "henkilöstöravintola":
            # Staff canteens at host institutions ("Henkilöstöravintola,
            # Terveyden ja hyvinvoinnin laitos (THL)", unit 8817): the site
            # is the venue. Appositive proper names ("Henkilöstöravintola,
            # ravintola Onnikka", unit 8796) and service descriptors stay whole.
            tail_base = re.sub(r"\s*\([^()]*\)$", "", tail.strip())
            if tail_base and re.search(self.INSTITUTION_TAIL_RE, tail_base.lower()):
                return head.strip(), tail.strip()
        if head.strip() and re.search(self.VENUE_WORDS_RE, tail.strip().lower()):
            return head.strip(), tail.strip()
        if (
            head.strip()
            and re.search(self.SCHOOL_HEAD_RE, head.strip().lower())
            and re.search(
                r"(kouluterveydenhuolto|opiskeluterveydenhuolto|opiskeluhuolto)$",
                tail.strip().lower(),
            )
        ):
            # Service at a school ("Kruununhaan yläasteen koulu,
            # kouluterveydenhuolto", unit 5664; "Kallion ala-aste,
            # kouluterveydenhuolto"): the service comes first, the school
            # is the venue. Mirrors the slash-pair rule above.
            return tail.strip(), head.strip()
        if head.strip() and re.search(r"\besiopetus$", tail.strip().lower()):
            if re.search(self.VENUE_WORDS_RE, head.strip().lower()):
                # "Tuohimäen päiväkoti, esiopetus": head is the venue.
                return head.strip(), None
            return head.strip(), tail.strip()
        return primary, None

    def _welfare_venue(self, unit, primary):
        ids = set(self._service_ids(unit))
        if (
            ids
            and ids <= self.WELFARE_NODES
            and re.search(
                r"(\w*(koulu|lyseo|lukio|opisto)\b|\b(skola(n)?|gymnasi\w*|daghem\w*)\b)",
                primary.strip().lower(),
            )
            and not any(word in primary.strip().lower() for word in ("terveydenhuol", "opiskeluhuol"))
        ):
            # Welfare office named after its host school (cf. Koivukylän koulu).
            return primary.strip()
        return None

    # Translated service designations appended to the venue (unit 70202:
    # en "Hämeenkylä School, school health care", sv "Hämeenkylä skola
    # skolhälsovård"). Stripped only with a remainder: bare "Elevhälsa"
    # stays a name.
    SERVICE_TAIL_RE = re.compile(
        r"(school health care|student health care|student welfare|pupil welfare"
        r"|skolhälsovård|studenthälsovård|elevhälsa|hälsovård för studerande)$",
        re.IGNORECASE,
    )

    def _chain_translation_text(self, text, fi_prefix):
        # Fi splits (or will split) this chain branch off ("Hemingway's
        # Tennispalatsi", unit 73568): strip the same tail from sv/en for
        # parity; the full form lands in official_name:sv/en below.
        if fi_prefix and (
            chain_match := re.match(re.escape(fi_prefix) + r"(?![A-Za-zÅÄÖåäö])", text, flags=re.IGNORECASE)
        ):
            if text[chain_match.end() :].strip(" ,-/–"):
                return fi_prefix
        return text

    def _bilingual_translation_text(self, text, fi_raw):
        # Bilingual translation fields ("Oodi 60 000 järvelle / The Ode
        # to the 60,000 Lakes", unit 23168): the fi prefix is not a venue;
        # keep the translated part.
        if fi_raw and text.lower().startswith((fi_raw + " / ").lower()):
            if rest := text[len(fi_raw) + 3 :].strip():
                return rest
        return text

    def _apply_translations(self, item, name):
        official = item["extras"].get("official_name", "")
        fi_venue = item.get("located_in") or ""
        # The fi chain split runs later in _apply_brand; resolve it here
        # from the still-full fi name so sv/en strip the same tail.
        fi_prefix, _fi_branch = self._chain_split(item.get("name") or "")
        for key in ("sv", "en"):
            raw = re.sub(self.ZW_CHARS, "", str(name.get(key) or "")).strip()
            text = raw
            if fi_venue and (
                text.lower().endswith((", " + fi_venue).lower()) or text.lower().endswith(("," + fi_venue).lower())
            ):
                # Same venue tail the fi split moved to located_in
                # ("Elevhälsa, Karhusuon koulu", unit 69678; missing-space
                # "Daycare Ankkalampi,Töölö - Duckies", unit 33747): strip
                # it for parity.
                text = text[: len(text) - len(fi_venue)].rstrip(" ,-/–").strip()
            if fi_venue:
                # Comma-less facility tails ("Park fältet Trädan Basketplan",
                # unit 42382): the trailing court/field/hall word is the name.
                match = self.FACILITY_TAIL_RE.search(text.lower())
                if match and match.start() > 0:
                    text = text[match.start() :].strip()
            service = self.SERVICE_TAIL_RE.search(text)
            if service and text[: service.start()].rstrip(" ,-/–").strip():
                text = text[: service.start()].rstrip(" ,-/–").strip()
            head, _, tail = text.rpartition(",")
            if head.strip() and self.COMMA_STREET_RE.search(tail.strip().lower()):
                # Same address tails fi drops ("Patotie 8", unit 74944):
                # structured street/housenumber carry them.
                text = head.strip()
            provider_split, provider_venue = self._split_provider_infix(text)
            if provider_venue:
                text = provider_split
                if "located_in" not in item:
                    item["located_in"] = provider_venue
            text = self._chain_translation_text(text, fi_prefix)
            text = self._bilingual_translation_text(text, re.sub(self.ZW_CHARS, "", str(name.get("fi") or "")).strip())
            if text and (text != item.get("name") or raw != text) and text != official:
                if re.match(r"^(vesiposti|vattenpost|water post)\b", text.lower()):
                    # Water posts: tails repeat the parsed street address.
                    text = re.split(r"[,/]", text, maxsplit=1)[0].strip()
                text = self._clean_name(text)
                # Feed glosses the venue type in en translations ("Juvanpuiston
                # koulu (school) / Disc golf course (3)", unit 50343): drop it.
                text = re.sub(r"\s*\(school\)", "", text, flags=re.IGNORECASE)
                facility, venue = self._split_facility(text)
                venue_name = item.get("name") or ""
                if venue and "located_in" not in item and venue != venue_name and venue_name not in venue:
                    # A venue identical to the name is the name itself, not
                    # a host (bilingual "Oodi 60 000 järvelle / The Ode ...",
                    # unit 23168, before the bilingual strip above).
                    if any(
                        word in venue.lower()
                        for word in (
                            "iltapäivätoiminta",
                            "eftermiddagsverksamhet",
                            "after-school activit",
                            "fter-school activit",
                            "opiskeluhuolto",
                            "opiskeluterveydenhuolto",
                            "kouluterveydenhuolto",
                            "esiopetus",
                            "elevhälsa",
                            "skolhälsovård",
                            "student welfare",
                            "school health",
                        )
                    ):
                        # Service-headed translation ("fter-school activities /
                        # Tahvonlahti ...", unit 76771, feed typo included):
                        # the venue slot holds the service, not a venue.
                        venue = None
                    else:
                        item["located_in"] = venue
                if facility:
                    if facility != item.get("name") and facility != fi_prefix:
                        # Chain-stripped translations equal the post-brand
                        # fi name, not the still-full applied name: suppress
                        # them like identical translations.
                        item["extras"][f"name:{key}"] = facility
                    if raw != facility:
                        # Transformed translation: keep the feed's full form
                        # alongside official_name like the fi raw, even when
                        # the useful part duplicates the name.
                        item["extras"][f"official_name:{key}"] = raw
                # Same name after cleaning, but keep the venue set above.

    def _apply_name(self, item, unit):
        name = unit.get("name") or {}
        if not isinstance(name, dict):
            return
        if self._apply_machine_name(item, name):
            return
        primary = name.get("fi") or name.get("sv") or name.get("en")
        if primary and str(primary).strip():
            raw_primary = re.sub(self.ZW_CHARS, "", str(primary)).strip()
            base_primary = raw_primary
            municipality = unit.get("municipality")
            if isinstance(municipality, str) and municipality.strip():
                # Municipality-headed names (unit 74116 "Lohja, Virkkalan
                # kirjasto") repeat the city field; official_name keeps the raw.
                muni_prefix = municipality.strip().casefold() + ","
                if base_primary.casefold().startswith(muni_prefix):
                    # Slice by the municipality's own length (casefold can
                    # change string length, so never slice by it).
                    base_primary = base_primary[len(municipality.strip()) + 1 :].strip()
            primary = self._clean_name(base_primary)
            if re.match(r"^vesiposti\b", primary.strip().lower()):
                # Tails repeat the parsed street address; collapse to the noun.
                primary, venue = "Vesiposti", None
            else:
                primary, venue = self._split_facility(primary)
            if not venue and "," in primary:
                primary, venue = self._split_comma_venue(primary)
            if not venue:
                provider_split, provider_venue = self._split_provider_infix(primary)
                if provider_venue:
                    primary, venue = provider_split, provider_venue
            if not venue and "," not in primary:
                if welfare := self._welfare_venue(unit, primary):
                    venue = welfare
                    primary = "Opiskeluhuolto"
            if venue:
                for prefix in (
                    "Iltapäivätoiminta / ",
                    "Eftermiddagsverksamhet / ",
                    "Finskspråkig eftermiddagsverksamhet / ",
                ):
                    if venue.startswith(prefix):
                        venue = venue[len(prefix) :].strip()
                        break
                if venue != primary:
                    item["located_in"] = venue
            if raw_primary != primary:
                # The feed's official designation, kept verbatim for
                # searchability; name holds the OSM-friendly short form.
                item["extras"]["official_name"] = raw_primary
            if re.search(r",\s*valaistu\s*$", raw_primary, re.IGNORECASE):
                # Lit trails ("Keimolan hiihtoharjoittelualue, valaistu",
                # unit 68639); the tail strips in _clean_name.
                item["extras"]["lit"] = "yes"
            item["name"] = primary
        self._apply_translations(item, name)

    # ---- Address handling: housenumber/unit token parsing, tail
    # ---- stripping, comma fallbacks, street/place/venue routing.
    def _apply_address(self, item, unit):
        item["country"] = "FI"
        municipality = unit.get("municipality")
        if isinstance(municipality, str) and municipality.strip():
            # Source stores municipalities lowercase; capitalise for output.
            item["city"] = municipality.strip().title()
        street = unit.get("street_address") or {}
        if isinstance(street, dict):
            address = street.get("fi") or street.get("sv") or street.get("en")
            if address and str(address).strip():
                self._apply_street_address(item, str(address).strip())
        postcode = unit.get("address_zip")
        if postcode is not None and str(postcode).strip():
            item["postcode"] = str(postcode).strip()

    # Address tails naming a place, not a street ("Iso Vasikkasaari",
    # "Silvolan tekojärvi"); these take addr:place, never addr:street.
    # Bare "ö" (Swedish for island) is safe here: numbered addresses parse
    # before suffixes run, single-token streets are claimed by STREET_SUFFIXES
    # first, and real street names end in -katu/-gata, never bare ö. All 86
    # ö-ending feed addresses are islands (cf. Stora Halsö, Järvö).
    PLACE_SUFFIXES = (
        "saari",
        "luoto",
        "niemi",
        "lahti",
        "järvi",
        "lampi",
        "koski",
        "joki",
        "kanava",
        "salmi",
        "puisto",
        "tori",
        "aukio",
        "kenttä",
        "metsä",
        "niitty",
        "pelto",
        "vaara",
        "mäki",
        "kallio",
        "asema",
        "ö",
        "holme",
        "holmen",
        "viken",
        "sjö",
        "sjön",
        "parken",
        "torget",
        "kari",
        "skär",
        "selkä",
        "laituri",
        "saaristo",
    )

    # Street suffixes for single-token addresses ("Teatteripolku" is a
    # street; "Harakka" without one is a place). Swedish forms included:
    # the feed is bilingual (cf. Kyrkslättsvägen).
    STREET_SUFFIXES = (
        "tie",
        "katu",
        "kuja",
        "polku",
        "väylä",
        "raitti",
        "ranta",
        "kaari",
        "penger",
        "esplanadi",
        "bulevardi",
        "vägen",
        "väg",
        "gatan",
        "gata",
        "gränden",
        "gränd",
        "stigen",
        "stig",
        "väli",
        "linja",
    )

    # Address tails naming a venue, not a street ("Hevoshaan päiväkoti",
    # "Kotilahden satama", "Luukin ulkoilualue"). No "asema": the place
    # routing above claims asema-endings first, so it would never fire here.
    VENUE_ADDRESS_WORDS = (
        "päiväkoti",
        "koulu",
        "lukio",
        "opisto",
        "kirjasto",
        "kirkko",
        "kappeli",
        "talo",
        "keskus",
        "toimisto",
        "virasto",
        "satama",
        "kartano",
        "torni",
        "koju",
        "vuori",
        "hautausmaa",
        "tarha",
        "tarhat",
        "puutarha",
        "paja",
        "palsta",
        "palstat",
        "alue",
        "leikkipuisto",
        "leikkipaikka",
        "puistikko",
        "daghem",
        "uimahalli",
    )
    # Venue compounds as one pattern, built once (cf. Sanomalan paviljonkikoulu).
    VENUE_ADDRESS_RE = re.compile(r"\w*(?:" + "|".join(VENUE_ADDRESS_WORDS) + r")\s*$")

    # Housenumber with optional letter and range ("Katutie 2a" stays whole,
    # "Nummentie 12 - 14" folds to "12-14").
    HOUSENUMBER_RE = re.compile(r"\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?")

    # Staircase/room/door tails after a housenumber, in priority order:
    # (min tokens, housenumber offset, middle, last, flags, join, note).
    STAIRCASE_RULES = (
        (4, 3, r"\d+[A-Za-z]?", r"[A-Za-z]{1,2}", 0, "MID LAST", "apartment + stair (Pursimiehenkatu 8 52 A)"),
        (4, 3, r"[A-Za-z]", r"\d+(?:-\d+)?[A-Za-z]?", 0, "MID LAST", "letter stair + number"),
        (4, 3, r"[A-Za-z]", r"[A-Za-z]", 0, "MID-LAST", "two letter stairs (Lummetie 2 B C)"),
        (
            3,
            2,
            None,
            r"[A-Za-z]{1,2}(?:-[A-Za-z]{1,2})?|\d+",
            0,
            "LAST",
            "letters, pair or apartment (BC, B-C, Sibeliuksenkatu 16 8)",
        ),
        (
            3,
            2,
            None,
            r"[A-Za-z]{1,2}\d+[A-Za-z]?|[A-Za-z]-(?:ovi|rappu)",
            re.IGNORECASE,
            "LAST",
            "room/door/staircase (R1, LH2, A-ovi, A-rappu)",
        ),
    )

    def _parse_staircase_unit(self, item, tokens):
        # Staircase, room and door tails after a housenumber ("Lummetie 2 BC",
        # "Työpajankatu 2 R1", "Sairaalatie 8 A-ovi", "Katu 5 A-rappu").
        number = self.HOUSENUMBER_RE
        for min_len, offset, mid, last, flags, join, _note in self.STAIRCASE_RULES:
            if len(tokens) < min_len:
                continue
            house = tokens[-offset]
            if not re.fullmatch(number, house):
                continue
            if mid is not None and not re.fullmatch(mid, tokens[-2]):
                continue
            if not re.fullmatch(last, tokens[-1], flags):
                continue
            item["housenumber"] = house
            if join == "MID LAST":
                item["unit"] = tokens[-2] + " " + tokens[-1]
            elif join == "MID-LAST":
                item["unit"] = tokens[-2] + "-" + tokens[-1]
            else:
                item["unit"] = tokens[-1]
            item["street"] = " ".join(tokens[:-offset])
            return True
        return False

    def _parse_address_tokens(self, item, tokens):
        number = self.HOUSENUMBER_RE
        tokens = [clean for t in tokens if (clean := t.strip().strip(",.;"))]
        if len(tokens) >= 3 and re.fullmatch(r"\d+", tokens[-3]) and re.fullmatch(r"[a-zåäö]", tokens[-2]):
            # Spaced housenumber letter ("Mannerheimintie 13 a A", unit
            # 26123; "Paasikuja 3 b A", unit 68882): the lowercase appendix
            # belongs to the number (13a), the last token is the staircase.
            # Staircases are uppercase, so uppercase middles never fold.
            tokens = tokens[:-3] + [tokens[-3] + tokens[-2]] + tokens[-1:]
        elif len(tokens) == 3 and re.fullmatch(r"\d+", tokens[-2]) and re.fullmatch(r"[a-zåäö]", tokens[-1]):
            # Same without a staircase ("Katu 5 a" shape, SYNTHETIC): a bare
            # trailing lowercase letter is the appendix, never a unit.
            tokens = tokens[:-2] + [tokens[-2] + tokens[-1]]
        if len(tokens) >= 2 and (paren := re.fullmatch(r"\(\s*([A-Za-z])\s*\)", tokens[-1])):
            # Parenthesised staircase ("Katu 5 (A)"): held back until a
            # housenumber confirms the address parses, so failures leave
            # no stray unit behind.
            paren_unit = paren.group(1)
            tokens = tokens[:-1]
        else:
            paren_unit = None
        if len(tokens) >= 2 and (dotted := re.fullmatch(r"(\d+)\.([A-Za-z]\.\d+)", tokens[-1])):
            # Dotted apartment tails ("Valhallankatu 4.A.9").
            item["housenumber"] = dotted.group(1)
            item["unit"] = dotted.group(2)
            item["street"] = " ".join(tokens[:-1])
            return True
        if (
            len(tokens) >= 4
            and re.fullmatch(number, tokens[-3])
            and tokens[-2] == "-"
            and re.fullmatch(number, tokens[-1])
        ):
            # Spaced housenumber range ("Nummentie 12 - 14").
            tokens = tokens[:-3] + [tokens[-3] + "-" + tokens[-1]]
        if self._parse_staircase_unit(item, tokens):
            return True
        if len(tokens) >= 2 and re.fullmatch(number, tokens[-1]):
            item["housenumber"] = tokens[-1]
            if paren_unit is not None:
                item["unit"] = paren_unit
            item["street"] = " ".join(tokens[:-1])
            return True
        if len(tokens) >= 2 and (match := re.fullmatch(r"(\d+[A-Za-z]+)(\d+[A-Za-z]*)", tokens[-1])):
            # "Arabianpolku 1A2": staircase A, apartment 2.
            item["housenumber"] = match.group(1)
            item["unit"] = match.group(2)
            item["street"] = " ".join(tokens[:-1])
            return True
        return False

    # Stripped tails describe everything but the street address. Order matters:
    # the comma floor rule must precede the bare-word rule, or
    # "Mannerheimintie 5, 2. krs" degrades to "Mannerheimintie 5, 2.".
    STRIP_RULES = (
        (r"\s*\((?![A-Za-z]\))[^)]*\)", 0, "parenthetical wings/floors (single-letter staircase spared)"),
        (r",\s*[\d\s&\.,-]*(krs|kerros|rak\.?|rakennus)\b.*$", 0, "comma floor/building tail"),
        (r"\s+\d+\.?\s*(krs|kerros)\b.*$", 0, "numbered floor tail"),
        (r"/\s*\d+\.?\s*(krs|kerros)\b.*$", 0, "slash floor tail"),
        (r"\s+(rak\.?|rakennus|krs|kerros)\b.*$", 0, "bare building/floor word"),
        (r"\s+(?:sisäpiha|kuisti)\b", re.IGNORECASE, "courtyard/porch word"),
        (r"\s+-\s*\d+(?:st|nd|rd|th)?\s*floor\b.*$", re.IGNORECASE, "English floor tail"),
        (r"\s+vastapäätä[\s.!]*$", re.IGNORECASE, "opposite-side note"),
        (
            r"\s+-\s*(sisään\w*|käynti\w*|sisäpiha|porras|ovi|entrance)\b.*$",
            re.IGNORECASE,
            "entrance tail",
        ),
        (r"\s+[-–]\s*$", 0, "trailing dash"),
        (r"\s*/\s*$", 0, "trailing slash"),
    )

    def _strip_address_base(self, address):
        # Parentheticals, floor/building tails and cross-street notes
        # describe everything but the street address; parse the base.
        if address.strip() in ("-", "–"):
            return ""
        # Soft hyphens are line-break artifacts (cf. Merikatu 8, unit 60729);
        # en/em dashes mark housenumber ranges (cf. Valimotie 17–19).
        address = address.replace("\u00ad", "").replace("–", "-").replace("—", "-")
        base = address
        for pattern, flags, _note in self.STRIP_RULES:
            base = re.sub(pattern, "", base, flags=flags).strip()
        return base

    def _apply_comma_address(self, item, address):
        # Visiting address wins: numbered last segment (Oodi, Töölönlahdenkatu 4),
        # else the head (Mikkolankuja 1, Oulunkylä), else a numbered middle
        # segment (Fleminginkatu 34 with a sisäpiha tail). True means handled.
        segs = [s.strip() for s in address.split(",") if s.strip()]
        if not segs:
            # Degenerate punctuation-only address: nothing to parse.
            return True
        tail = re.sub(r"^(käyntiosoite|besöksadress):?\s*", "", segs[-1], flags=re.IGNORECASE).strip()
        if re.search(r"\d", tail) and self._parse_address_tokens(item, tail.split()):
            return True
        if re.search(r"\d", segs[0]) and self._parse_address_tokens(item, segs[0].split()):
            if "unit" not in item and re.fullmatch(r"[A-Za-z](?:-ovi|-rappu)?", tail, re.IGNORECASE):
                # Door/staircase tail alongside a numbered head
                # ("Sairaalatie 8, A-ovi"); districts never match this shape.
                item["unit"] = tail
            elif "unit" not in item and (paren := re.fullmatch(r"\(\s*([A-Za-z])\s*\)", tail)):
                # Parenthesised staircase tail ("Sairaalatie 8, (A)").
                item["unit"] = paren.group(1)
            return True
        for seg in reversed(segs[1:-1]):
            # Middle segments, last first; head and tail tried above, and
            # value-comparison would skip distinct same-valued segments.
            if re.search(r"\d", seg) and self._parse_address_tokens(item, seg.split()):
                return True
        if not re.search(r"\d", address):
            # Place parts, no numbers ("Iso Mustasaari, Suomenlinna").
            item["extras"]["addr:place"] = address
            return True
        return self._parse_address_tokens(item, address.split())

    def _apply_street_address(self, item, address):
        # "Aarnivalkeantie 9 E" is street + housenumber + staircase unit;
        # "Katutie 2a" is a whole housenumber, never split the letter off.
        # Finnish floor numbers don't convert to OSM level, so they are dropped.
        address = self._strip_address_base(address)
        if not address:
            return
        if re.search(r"\d\s+-\s+[A-Za-zåäöÅÄÖ]", address):
            # Cross-street descriptions ("Katu 5 - Katu 6"): a number left
            # of the dash with letters right names two streets, hence no
            # single housenumber. Descriptor tails ("... Center -
            # katutaso") have no number on the left and still parse below.
            # Spaced number ranges ("Nummentie 12 - 14") and compact ones
            # ("Valimotie 17-19") never match, so they parse too.
            item["street_address"] = address
            return
        tokens = address.split()
        if "," in address:
            if self._apply_comma_address(item, address):
                return
        elif self._parse_address_tokens(item, tokens):
            return
        stripped = list(tokens)
        while len(stripped) >= 3 and re.fullmatch(r"[A-Za-zåäöÅÄÖ-]{3,}", stripped[-1]):
            # Trailing district words ("Ratakatu 6 Kaartinkaupunki Helsinki").
            if self._parse_address_tokens(item, stripped[:-1]):
                return
            stripped = stripped[:-1]
        if len(tokens) == 1:
            if tokens[0].lower().endswith(self.STREET_SUFFIXES):
                item["street"] = tokens[0]
            else:
                item["extras"]["addr:place"] = address
            return
        has_number = re.search(r"\d", address)
        if not has_number and " - " in address:
            # Cross-street descriptions name no single street.
            item["street_address"] = address
            return
        if not has_number and tokens[-1].lower().endswith(self.STREET_SUFFIXES):
            # Bare street, no number ("Urho Kekkosen katu").
            item["street"] = address
            return
        if tokens[-1].lower().endswith(self.PLACE_SUFFIXES):
            if tokens[-1].lower().endswith(("asema", "selkä", "laituri")) and not has_number:
                # Stations, open water and piers are not postal addr:place values.
                item["street_address"] = address
            else:
                # Overlap words (asema is in both lists) route to place, never located_in.
                item["extras"]["addr:place"] = address
        elif re.search(self.VENUE_ADDRESS_RE, address.lower()) or re.match(
            r"(leikkipuisto|leikkipaikka)\b", address.lower()
        ):
            # Venue-headed, not a located_in host: located_in is reserved for
            # the name-split facility-in-venue relation.
            item["street_address"] = address
        else:
            item["street_address"] = address

    # ---- Operator, brand, contact, parking. organizer_name precedes
    # ---- departments; tenants never inherit city operators.
    ORGANIZER_JUNK_EXACT = ("yksityinen", "valtio")
    # Feed truncation artifact doubling the name (cf. Montessori-leikkikoulu).
    ORGANIZER_DUP_RE = re.compile(r"^(.{25,}?)\s*r\s*\1\s*y$", re.IGNORECASE)

    def _clean_organizer_name(self, organizer):
        # Returns the operator name, or None for junk/missing organizers.
        clean = organizer.strip() if isinstance(organizer, str) else ""
        folded = clean.casefold()
        if (
            not clean
            or folded in self.ORGANIZER_JUNK_EXACT
            or "yksityinen palveluntuottaja" in folded
            or re.search(r"\byksityise", folded)
        ):
            return None
        operator = clean
        if dup := self.ORGANIZER_DUP_RE.match(operator):
            suffix = " ry" if operator.strip().lower().endswith("y") else ""
            operator = dup.group(1).strip() + suffix
        if operator.casefold() == "valtion rautatiet":
            # Archaic name for the state railway (cf. Tuomarilan asema,
            # filed directly under Suomen valtio); normalize to the
            # current name so sibling stations agree.
            operator = "Suomen valtio"
        return operator

    def _resolve_operator_name(self, unit):
        # organizer_name first (the true operator, e.g. an NGO club), then
        # root department, then direct department. Generic values are junk.
        if operator := self._clean_organizer_name(unit.get("organizer_name")):
            return operator
        root_department = unit.get("root_department")
        department = unit.get("department")
        if isinstance(root_department, str) and self.departments.get(root_department):
            return self.departments.get(root_department)
        if isinstance(department, str):
            return self.departments.get(department)
        return None

    def _finish_operator(self, item, unit, operator):
        if operator.casefold().replace(" ", "") in ("pilkepäiväkoditoy", "pilkepäiväkodit"):
            # Canonical form; feed spellings vary.
            operator = "Pilke päiväkodit Oy"
        if operator in self.CITY_OPERATORS:
            municipality = unit.get("municipality")
            if not (isinstance(municipality, str) and municipality.strip()):
                # No municipality to confirm against; skip.
                self._stat("operator/no_municipality")
                return
            if municipality.strip().title() != self.CITY_OPERATORS[operator]:
                # A city cannot operate in another city (Espoon teatteri).
                self._stat("operator/mismatch")
                return
        item["operator"] = operator
        qid = self.operators_wikidata.get(operator)
        if qid is None:
            bare = re.sub(r"\s*\(.*\)\s*$", "", operator).strip()
            qid = self.operators_wikidata.get(bare)
        if qid is not None:
            item["operator_wikidata"] = qid

    # Provider tails that name the legal operator (feed spells short).
    # Unknown tails (Beanet Oy, caterers) never promote: only mapped ones.
    # Keys are folded without dots/spaces ("r.y." vs "ry" spellings).
    PROVIDER_OPERATORS = {
        "puuhalaoy": "Puuhala iltapäiväkerhot Oy",
        "helsinginnuortenmiestenkristillinenyhdistysry": "Helsingin Nuorten Miesten Kristillinen Yhdistys r.y.",
        "sporttiiltapäiväkerhotoy": "Sportti Iltapäiväkerhot Oy",
    }

    OWNERSHIP_TAIL_RE = re.compile(r",\s*(yksityinen|yksityiset|privat|private)\.?$", re.IGNORECASE)

    def _has_ownership_tail(self, unit):
        name = unit.get("name") or {}
        fi = str(name.get("fi") or "") if isinstance(name, dict) else ""
        return bool(self.OWNERSHIP_TAIL_RE.search(fi.strip()))

    def _provider_tail_operator(self, unit):
        name = unit.get("name") or {}
        fi = str(name.get("fi") or "") if isinstance(name, dict) else ""
        # Stripped: a trailing space breaks the end anchor below.
        match = re.search(r",\s*([^,]*\b(r\.y\.|ry|oy|ab)\.?)$", fi.strip(), flags=re.IGNORECASE)
        if not match:
            return None
        return self.PROVIDER_OPERATORS.get(re.sub(r"[\s.]+", "", match.group(1)).lower())

    def _apply_operator(self, item, unit):
        # Tenants (shops, eateries, hotels, cinemas, canteens): the department
        # only maintains the record (Kino Tapiola is not run by the city).
        # Tenant organizers are not promoted either; brand + operator:type
        # carry the attribution.
        is_tenant = bool(
            item.get_tag("shop")
            or item.get_tag("amenity") in ("restaurant", "cafe", "bar", "fast_food", "cinema", "canteen")
            or item.get_tag("tourism") == "hotel"
        )
        if not self._clean_organizer_name(unit.get("organizer_name")) and (
            provider := self._provider_tail_operator(unit)
        ):
            # Known provider runs the unit (Puuhala afternoon clubs, unit
            # 74329); the department only keeps the record.
            self._finish_operator(item, unit, provider)
            item["extras"]["operator:type"] = "private"
            self._stat("operator/private")
            return
        if not self._clean_organizer_name(unit.get("organizer_name")):
            name = unit.get("name") or {}
            fi = str(name.get("fi") or "") if isinstance(name, dict) else ""
            if (identity := self._provider_infix_identity(fi)) and self._split_provider_infix(fi)[1]:
                # Embedded provider runs the unit (Terveystalo Otaniemi on
                # the Aalto campus, unit 50608).
                brand, qid = identity
                item["operator"] = brand
                item["operator_wikidata"] = qid
                item["extras"]["operator:type"] = "private"
                self._stat("operator/private")
                return
        # The feed flags private services itself; a city is never their operator.
        if unit.get("displayed_service_owner_type") in (
            "PRIVATE_SERVICE",
            "VOUCHER_SERVICE",
            "PRIVATE_CONTRACT_SCHOOL",
        ):
            if not is_tenant:
                # Tenant-private records are private by type but not counted.
                self._stat("operator/private")
            item["extras"]["operator:type"] = "private"
            return
        if is_tenant:
            # Tenants are private operators by definition; brand carries
            # the name, operator:type the privateness.
            item["extras"]["operator:type"] = "private"
            return
        if self._has_ownership_tail(unit):
            # Register flag, not a name ("Daghemmet Fyndet Kanel,
            # yksityinen", unit 64929): private whatever the feed flag says.
            item["extras"]["operator:type"] = "private"
            if self._clean_organizer_name(unit.get("organizer_name")) and (
                operator := self._resolve_operator_name(unit)
            ):
                self._finish_operator(item, unit, operator)
            else:
                # No organizer: a city department never operates a private
                # unit (cf. Steiner school 75921, filed under the city).
                self._stat("operator/private")
            return
        if operator := self._resolve_operator_name(unit):
            self._finish_operator(item, unit, operator)
        elif "operator" not in item:
            # Department miss or junk organizer; visible on drift watch.
            self._stat("operator/unattributed")

    def _apply_brand(self, item, unit):
        # Private chains known by QID. fi only: sv/en re-split generic words
        # ("Ilon Pilke", unit 48494) into false hits.
        organizer = unit.get("organizer_name") or ""
        name = unit.get("name") or {}
        text = (
            (str(organizer) + " " + str((name.get("fi") or ""))).lower()
            if isinstance(name, dict)
            else str(organizer).lower()
        )
        for keyword, brand, qid, match in self.CHAIN_BRANDS:
            if self._match_brand_keyword(keyword, match, text):
                if brand == "Pääkaupunkiseudun Kierrätyskeskus" and (
                    "stara" in text or "vaarallinen" in text or "lohja" in text
                ):
                    # Generic recycling-centre words used by others (Stara, Lohja).
                    continue
                item["brand"] = brand
                item["brand_wikidata"] = qid
                break
        self._apply_chain_branch(item, unit)

    # Chains whose every feed unit is shaped "Brand separator Branch"
    # (verified uniform per chain, one row each): split the branch off
    # into branch=*. Store-type branches never split ("Partioaitta
    # Outlet" keeps its full name). Non-uniform chains (Pilke, Norlandia,
    # Dylan, Factory) and generic words shared by independent shops
    # (Antikvariaatti, Lankakauppa) are deliberately absent, as are
    # collision shapes: bare "Sokos" would catch the Sokos Hotel gym
    # (unit 53941), and "Cafe Tarina" would catch the bakery unit 79479
    # ("Leipomo & Myymälä" is a descriptor, not a site).
    CHAIN_SPLITS = (
        "Jungle Juice Bar",
        "Kanniston Leipomo",
        "Hanko Aasia",
        "Paperikauppa Putinki",
        "Pizzeria Via Tribunali",
        "Levain",
        "Fazer Café",
        "UFF",
        "Fida secondhand",
        "Metrosuutarit",
        "Fonum",
        "SPR Kontti",
        "Picnic",
        "Musti ja Mirri",
        "Musti ja Murri",
        "Robert's Coffee",
        "24 Pesula",
        "Eat Poke",
        "Kultajousi",
        "Laatukoru",
        "Arnolds",
        "Partioaitta",
        "Kidia",
        "William K.",
        "Omena-hotelli",
        "Tortilla House",
        "Deliberi",
        "Ruohonjuuri",
        "Sizzle Station",
        "Finnfoto Galleria",
        "Bär Bar",
        "Mashiro",
        "Uuno",
        "VillageWorks",
        "Meeting Park",
        "Innovation Home",
        "Putte's Bar & Pizza",
        "Boneless",
        "Friends & Brgrs",
        "Gateau",
        "Makaronitehdas",
        "Suomalainen Kirjakauppa",
        "Classic Pizza Restaurant",
        "Noodle Story",
        "Hemingway's",
        "Delhi Rasoi",
        "Burger Company",
        "Brewster Bar",
        "Oishi18",
        "Ristorante Limone",
        "Bambu Sushi",
        "The Pantry",
        "The Body Shop",
        "Marimekko",
        "Tortilla Corner",
        "Joe & the Juice",
        "Aimo Park",
        "EuroPark",
        "Finnkino",
        "Scandic",
        "Clarion Hotel",
        "Comfort Hotel",
        "Holiday Inn",
        "Original Sokos Hotel",
        "Solo Sokos Hotel",
        "Break Sokos Hotel",
        "GLO Hotel",
        "Hiisi Hotel",
        "Hiisi Homes & Hotel",
        "Forenom Aparthotel Helsinki",
        "Forenom Serviced Apartments Helsinki",
        "Forenom Hostel Helsinki",
        "Radisson Blu Hotel",
        "Radisson Blu Seaside Hotel",
        "Radisson Blu Royal Hotel",
        "Radisson Blu Plaza Hotel",
        "Radisson Blu Aleksanteri Hotel",
        "Radisson RED",
        "Citybox Hotel",
        "Hotel Indigo",
        "The Folks Hotel",
        "Lapland Hotels",
        "Home Hotel",
        "Crowne Plaza",
        "Ravintola Loru",
        "Ravintola Konnichiwa",
        "Krung Thep Thai Bistro",
        "Ravintola MoMo",
        "Ravintola Rioni",
        "Fat Lizard",
        "Rosso Pizza",
        "Amarillo",
        "Ravintola Haiku",
        "Stockmann",
        "Rusta",
        "Puuilo",
        "Food Market Herkku",
        "NP Housukauppa",
        "Moomin Shop",
        "Heirol Shop",
        "Sinelli-myymälä",
    )

    def _chain_split(self, name):
        # "Brand separator Branch" split shared by _apply_chain_branch and
        # translation parity: (None, None) when the name stays whole.
        for prefix in self.CHAIN_SPLITS:
            if not re.match(re.escape(prefix) + r"(?![A-Za-zÅÄÖåäö])", name, re.IGNORECASE):
                continue
            branch = name[len(prefix) :].strip(" ,-/–:")
            outlet = branch.casefold()
            if not branch or outlet == "outlet" or outlet.startswith("outlet ") or outlet.startswith("outlet-"):
                # "Partioaitta Outlet" (or "Outlet Helsinki") is a store
                # type, not a branch site: keep the full name.
                return None, None
            if "(" in branch or "talkoolaituri" in outlet:
                # Paren qualifiers name a sub-unit, not a site ("Finnkino
                # Tennispalatsi (Finnkino Yritysmyynti)", unit 20989); a
                # talkoolaituri remainder is a tool-library record filed
                # under a hotel name ("Comfort Hotel Sellon
                # talkoolaituri", unit 79884). Keep the full name.
                return None, None
            return prefix, branch
        return None, None

    def _apply_chain_branch(self, item, unit):
        # OSM names the branch separately (branch=*): "Aimo Park, Vallila"
        # becomes name plus branch (unit 67707 shape). Runs on the applied
        # name, so comma-venue and translation splits happen first.
        name = item.get("name") or ""
        prefix, branch = self._chain_split(name)
        if not prefix:
            return
        if "official_name" not in item["extras"]:
            item["extras"]["official_name"] = item["name"]
        item["name"] = prefix
        item["branch"] = branch
        return

    def _normalize_website(self, www):
        # Feed omits the scheme. Known-bad feed hostnames pass through and
        # the pipeline drops just the website field (website/invalid):
        # comma typo unit 66055 plus punycode units 68883/64153/47295.
        if isinstance(www, str) and www.strip():
            www = {"fi": www.strip()}
        if not isinstance(www, dict):
            return None
        invalid = False
        for key in ("fi", "sv", "en"):
            # A bad fi website must not block a good sv/en one.
            raw = www.get(key)
            if not (isinstance(raw, str) and (website := raw.strip())):
                continue
            if "://" not in website:
                website = "https://" + website.lstrip("/")
            scheme, _, host = website.partition("://")
            if scheme.lower() in ("http", "https") and "." in host:
                if self._valid_hostname(urlparse(website).hostname):
                    return website
                # Known feed faults the pipeline fails the build on (comma-typo
                # unit 66055, punycode units 68883/64153/47295): try the next
                # language before dropping the field.
                invalid = True
                continue
            # Unusable scheme (cf. ftp://): counted, then the next language.
            invalid = True
            continue
        if invalid:
            self._stat("website/invalid")
        return None

    @staticmethod
    def _valid_hostname(hostname):
        # Mirrors CheckItemPropertiesPipeline._is_valid_hostname, including
        # its explicit Punycode rejection.
        if not hostname or len(hostname) > 253:
            return False
        for part in hostname.split("."):
            if not part or len(part) > 63:
                return False
            if part.startswith("-") or part.endswith("-"):
                return False
            if part.lower().startswith("xn--"):
                return False
            for ch in part:
                cat = unicodedata.category(ch)
                if not (cat.startswith("L") or cat == "Nd" or ch == "-"):
                    return False
        return True

    def _normalize_email(self, email):
        # De-obfuscate "a (at) b dot fi".
        if not isinstance(email, str):
            return None
        value = email.strip()
        value = re.sub(r"^mailto:", "", value, flags=re.IGNORECASE)
        value = re.sub(r"\(at\)|\[at\]| at ", "@", value, flags=re.IGNORECASE)
        value = re.sub(r"\(dot\)|\[dot\]| dot ", ".", value, flags=re.IGNORECASE)
        value = value.replace(" ", "").replace(chr(0xFEFF), "")
        if "@" in value and "." in value.split("@")[-1]:
            return value
        return None

    def _apply_contact(self, item, unit):
        # Municipal contacts repeat across units (one phone/email serves
        # many schools/clinics): low uniqueness is the dataset, not dupes.
        if website := self._normalize_website(unit.get("www")):
            item["website"] = website
        phone = unit.get("phone")
        if isinstance(phone, str) and (phone := phone.strip()):
            item["phone"] = phone
        elif isinstance(phone, list):
            phones = [stripped for p in phone if (stripped := str(p).strip())]
            if phones:
                item["phone"] = phones[0]
        email = self._normalize_email(unit.get("email"))
        if email is not None:
            item["email"] = email

    def _apply_media(self, item, unit):
        # Picture endpoint, when the feed sets one. Placeholders repeat
        # across units, so low image uniqueness is expected. Dead picture
        # URLs pass through (cf. unit 15358, 403 on both browser and API
        # fetch while 4/4 sampled siblings return 200): no feed signal
        # distinguishes them, and crawl-time probing would break the CI
        # time budget.
        picture = unit.get("picture_url")
        if isinstance(picture, str) and picture.strip():
            item["image"] = picture.strip()

    # LIPAS data (unit.extra). Measured surface wins over name-inferred.
    LIPAS_SURFACES = {
        "asfaltti": "asphalt",
        "hiekka": "sand",
        "hiekkatekonurmi": "artificial_turf",
        "tekonurmi": "artificial_turf",
        "nurmi": "grass",
        "sora": "gravel",
        "kivituhka": "fine_gravel",
        "tiilimurska": "gravel",
        "betoni": "concrete",
        "puu": "wood",
        "hake": "woodchips",
    }

    def _apply_lipas_extras(self, item, unit):
        extra = unit.get("extra")
        if not isinstance(extra, dict):
            return
        surface = extra.get("lipas.surfaceMaterial")
        if isinstance(surface, str) and surface.strip().lower() in self.LIPAS_SURFACES:
            item["extras"]["surface"] = self.LIPAS_SURFACES[surface.strip().lower()]
        if str(extra.get("lipas.ligthing") or extra.get("lipas.lighting") or "").strip() == "1":
            # The feed spells the key "ligthing"; accept the correct
            # spelling too so a feed fix cannot silently drop lit.
            item["extras"]["lit"] = "yes"
        if str(extra.get("lipas.toilet") or "").strip() == "1":
            item["extras"]["toilets"] = "yes"

    def _apply_parking_capacity(self, item, unit):
        # Descriptions like "5 pysäköintipaikkaa" or "3 esteetöntä autopaikkaa".
        # Bare "LP" is an internal series code, not liityntäpysäköinti:
        # 139 LP lots scatter across Espoo with plain P signage (cf. Arvelantie).
        name = unit.get("name") or {}
        name_text = (
            (str(name.get("fi") or "") + " " + str(name.get("sv") or "")).lower() if isinstance(name, dict) else ""
        )
        if "liitynt" in name_text or "anslutningsparkering" in name_text:
            item["extras"]["park_ride"] = "yes"
        description = unit.get("description") or {}
        if not isinstance(description, dict):
            return
        text = str(description.get("fi") or "").strip().lower().rstrip(".)")
        match = re.search(
            r"(\d+)\s+(esteetön(?:tä|ten)?\s+)?(autopaikkaa?|pysäköintipaikkaa?|paikkaa?|p-paikkaa?)",
            text,
        )
        if not match:
            # Reversed counts ("Pysäköintipaikkoja: 165", unit 67671).
            match = re.search(r"(?:pysäköinti|auto|p-)?paikkoja?:\s*(\d+)", text)
            if match:
                item["extras"]["capacity"] = match.group(1)
                self._stat("parking/capacity")
            disabled = re.search(r"inva-paikat:\s*(\d+)", text)
            if disabled and int(disabled.group(1)) > 0:
                item["extras"]["capacity:disabled"] = disabled.group(1)
                item["extras"]["wheelchair"] = "designated"
            if not match and not disabled:
                self._stat("parking/no_capacity")
            return
        if match.group(2):
            # Accessible-only count: no total capacity.
            item["extras"]["capacity:disabled"] = match.group(1)
            item["extras"]["wheelchair"] = "designated"
        else:
            item["extras"]["capacity"] = match.group(1)
            if "esteetön" in name_text:
                item["extras"]["wheelchair"] = "designated"
        self._stat("parking/capacity")

    # ---- Sport inference and name rescue for untabled units.
    PITCH_SPORTS = (
        ("amerikkalainen jalkapallo", Sport.AMERICAN_FOOTBALL),
        ("amer. jalkapallo", Sport.AMERICAN_FOOTBALL),
        ("amer jalkapallo", Sport.AMERICAN_FOOTBALL),
        ("jalkapallo", Sport.SOCCER),
        ("futsal", Sport.SOCCER),
        ("koripallo", Sport.BASKETBALL),
        ("katukoris", Sport.BASKETBALL),
        ("pöytätennis", Sport.TABLE_TENNIS),
        ("tennis", Sport.TENNIS),
        ("padel", Sport.PADEL),
        ("lentopallo", Sport.VOLLEYBALL),
        ("beachvolley", Sport.BEACH_VOLLEYBALL),
        ("beach volley", Sport.BEACH_VOLLEYBALL),
        ("rantalentopallo", Sport.BEACH_VOLLEYBALL),
        ("beachfutis", Sport.SOCCER),
        ("rantafutis", Sport.SOCCER),
        ("pesäpallo", Sport.BASEBALL),
        ("sulkapallo", Sport.BADMINTON),
        ("salibandy", Sport.FLOORBALL),
        ("sähly", Sport.FLOORBALL),
        ("innebandy", Sport.FLOORBALL),
        ("käsipallo", Sport.HANDBALL),
        ("rugby", Sport.RUGBY),
        ("kriketti", Sport.CRICKET),
    )

    # Playing surfaces, e.g. hiekkakenttä. Hybrids first: hiekkatekonurmi
    # is sand-dressed turf, tekonurmi beats plain nurmi the same way.
    PITCH_SURFACES = (
        ("tekonurmi", "artificial_turf"),
        ("nurmi", "grass"),
        ("hiekka", "sand"),
        ("asfaltti", "asphalt"),
        ("sora", "gravel"),
    )
    # District names that merely contain a surface word (Hiekkaharju,
    # Nurmijärvi) must not tag the surface. Stems, not base forms:
    # inflections like Nurmijärven contain the stem but not the base.
    SURFACE_DISTRICTS = {"nurmi": "nurmijärv", "hiekka": "hiekkaharju"}

    # Specific beats generic: pöytätennis contains tennis.
    SPORT_OVERRIDES = (
        (Sport.TABLE_TENNIS, Sport.TENNIS),
        (Sport.BEACH_VOLLEYBALL, Sport.VOLLEYBALL),
        (Sport.AMERICAN_FOOTBALL, Sport.SOCCER),
    )

    def _earliest(self, rules):
        # Earliest tabled rule wins over tree nearness.
        return min(rules, key=lambda r: self.rule_precedence[r])

    def _city_info_kind(self, text):
        # Info desks with no tabled node (HSL Vantaa-info, Espoo-info).
        # information=office: tourist_information is not a documented value.
        if "matkailuneuvonta" in text or "tourist information" in text:
            return "office"
        if re.search(r"\b(espoo|vantaa|helsinki)-?info\b", text) and not (
            "työllisyyspalvelut" in text or "international house" in text
        ):
            return "office"
        return None

    def _names_lower(self, unit):
        # fi/sv/en name blob for substring matching.
        name = unit.get("name") or {}
        if not isinstance(name, dict):
            return "", "", ""
        return (
            str(name.get("fi") or "").lower(),
            str(name.get("sv") or "").lower(),
            str(name.get("en") or "").lower(),
        )

    def _refine_text(self, unit):
        # Table refinements must see every language: Swedish-only and
        # English-only names otherwise bypass all noun tables.
        fi, sv, en = self._names_lower(unit)
        return (fi + " " + sv + " " + en).strip()

    def _infer_sports(self, text):
        # Substring match plus specific-beats-generic overrides, shared by
        # the initial pitch pass and the ice-rink fixup below.
        sports = [sport for keyword, sport in self.PITCH_SPORTS if keyword in text]
        for specific, generic in self.SPORT_OVERRIDES:
            if specific in sports:
                sports = [s for s in sports if s != generic]
        return sports

    def _apply_pitch_sport(self, item, unit):
        name = unit.get("name") or {}
        if not isinstance(name, dict):
            return
        text = self._refine_text(unit)
        if sports := self._infer_sports(text):
            add_sport(sports, item)
        for keyword, surface in self.PITCH_SURFACES:
            excluded = self.SURFACE_DISTRICTS.get(keyword)
            if keyword in text and (excluded is None or excluded not in text):
                item["extras"]["surface"] = surface
                break

    # (substring, rescue category, refine category). Rescue serves untabled
    # units, refine corrects tabled ones; None means one path only. First
    # substring wins within each view, so row order is the priority order:
    # feed renames can silently re-tag (unit 78911 Kahvila-ravintola rides
    # on kahvila < ravintola). New nouns need a test pin and a harness diff.
    NOUN_TABLE = (
        ("trimmaamo", Categories.SHOP_PET_GROOMING, None),
        ("talkoolaituri", Categories.TOOL_LIBRARY, Categories.TOOL_LIBRARY),
        ("vesiurheilukeskus", Categories.LEISURE_SPORTS_CENTRE, Categories.LEISURE_SPORTS_CENTRE),
        ("kahvila", Categories.CAFE, Categories.CAFE),
        ("cafe", Categories.CAFE, Categories.CAFE),
        ("ravintola", Categories.RESTAURANT, Categories.RESTAURANT),
        ("kukkakauppa", Categories.SHOP_FLORIST, None),
        ("kukkatalo", Categories.SHOP_FLORIST, None),
        ("kukkakammari", Categories.SHOP_FLORIST, None),
        ("taikakukka", Categories.SHOP_FLORIST, None),
        # Both spellings occur in the feed (cf. Musti ja Mirri, Musti ja Murri Munkkivuori).
        ("musti ja mirri", Categories.SHOP_PET, None),
        ("musti ja murri", Categories.SHOP_PET, None),
        ("lemmikki", Categories.SHOP_PET, None),
        ("kultajousi", Categories.SHOP_JEWELRY, None),
        ("laatukoru", Categories.SHOP_JEWELRY, None),
        ("kulta-aika", Categories.SHOP_JEWELRY, None),
        ("jewel", Categories.SHOP_JEWELRY, None),
        ("marimekko", Categories.SHOP_CLOTHES, None),
        ("outlet", Categories.SHOP_CLOTHES, None),
        ("menswear", Categories.SHOP_CLOTHES, None),
        ("coffee", Categories.CAFE, None),
        ("gateau", Categories.CAFE, None),
        ("vintage", Categories.SHOP_SECOND_HAND, None),
        ("kirppis", Categories.SHOP_SECOND_HAND, Categories.SHOP_SECOND_HAND),
        ("kirpputori", Categories.SHOP_SECOND_HAND, Categories.SHOP_SECOND_HAND),
        ("kierrätyskeskus", Categories.SHOP_SECOND_HAND, Categories.SHOP_SECOND_HAND),
        ("secondhand", Categories.SHOP_SECOND_HAND, Categories.SHOP_SECOND_HAND),
        ("second hand", Categories.SHOP_SECOND_HAND, Categories.SHOP_SECOND_HAND),
        ("kamerakauppa", Categories.SHOP_PHOTO, None),
        ("lankakauppa", Categories.SHOP_CRAFT, None),
        ("kenkäpesula", Categories.SHOP_SHOE_REPAIR, None),
        ("kodinkonehuolto", Categories.CRAFT_ELECTRONICS_REPAIR, None),
        ("tietokonehuolto", Categories.CRAFT_ELECTRONICS_REPAIR, None),
        ("puhelinhuolto", Categories.CRAFT_ELECTRONICS_REPAIR, None),
        ("huoltoliike", Categories.CRAFT_ELECTRONICS_REPAIR, None),
        ("lainaamo", Categories.TOOL_LIBRARY, None),
        ("lakritsi", Categories.SHOP_CONFECTIONERY, None),
        ("pakohuone", Categories.LEISURE_ESCAPE_GAME, None),
        ("escape", Categories.LEISURE_ESCAPE_GAME, None),
        ("melontapiste", Categories.AMENITY_BOAT_RENTAL, Categories.AMENITY_BOAT_RENTAL),
        ("leikkipaikka", Categories.LEISURE_PLAYGROUND, None),
        ("kirjasto", None, Categories.LIBRARY),
        ("bibliotek", None, Categories.LIBRARY),
        ("lippumyymälä", Categories.SHOP_TICKET, None),
        ("lipunmyynti", Categories.SHOP_TICKET, None),
        ("musiikkikoulu", Categories.MUSIC_SCHOOL, Categories.MUSIC_SCHOOL),
        ("anime", Categories.SHOP_ANIME, None),
        ("taidekauppa", Categories.SHOP_ART, None),
        ("taidetarvik", Categories.SHOP_ART, None),
        ("taidegalleria", Categories.SHOP_ART, None),
        ("leipomo", Categories.SHOP_BAKERY, Categories.SHOP_BAKERY),
        ("konditoria", Categories.SHOP_BAKERY, Categories.SHOP_BAKERY),
        ("bakery", Categories.SHOP_BAKERY, Categories.SHOP_BAKERY),
        ("kakkugalleria", Categories.SHOP_BAKERY, Categories.SHOP_BAKERY),
        ("kuvataidekoulu", Categories.SCHOOL, Categories.SCHOOL),
        ("kirjakauppa", Categories.SHOP_BOOKS, None),
        ("pelikauppa", Categories.SHOP_GAMES, None),
        ("lelukauppa", Categories.SHOP_TOYS, None),
        ("pelago", Categories.SHOP_BICYCLE, None),
        ("seven art", Categories.SHOP_ART, None),
        ("perheneuvola", Categories.SOCIAL_FACILITY_OUTREACH, Categories.SOCIAL_FACILITY_OUTREACH),
        ("neuvola", Categories.CLINIC, None),
        ("venevuokraus", Categories.AMENITY_BOAT_RENTAL, None),
        ("viljelypalsta", Categories.ALLOTMENTS, None),
        ("pesula", Categories.SHOP_LAUNDRY, None),
        ("jokamiesgolf", Categories.LEISURE_GOLF_COURSE, None),
        ("seikkailugolf", Categories.LEISURE_MINIATURE_GOLF, Categories.LEISURE_MINIATURE_GOLF),
        ("yths", None, Categories.CLINIC),
        ("2hand", None, Categories.SHOP_SECOND_HAND),
        ("opshop", None, Categories.SHOP_SECOND_HAND),
        ("arena center", None, Categories.LEISURE_SPORTS_CENTRE),
        ("luontokeskus", None, Categories.MUSEUM),
        ("verhoomo", None, Categories.CRAFT_UPHOLSTERER),
        ("verhoilu", None, Categories.CRAFT_UPHOLSTERER),
        ("bowling", None, Categories.LEISURE_BOWLING_ALLEY),
        ("keilahalli", None, Categories.LEISURE_BOWLING_ALLEY),
        ("keilarata", None, Categories.LEISURE_BOWLING_ALLEY),
        ("eräkämppä", None, Categories.TOURISM_WILDERNESS_HUT),
        ("autiotupa", None, Categories.TOURISM_WILDERNESS_HUT),
        ("kahluuall", None, Categories.LEISURE_PADDLING_POOL),
        ("siirtolapuutarha", Categories.ALLOTMENTS, Categories.ALLOTMENTS),
        ("skeittihalli", None, Categories.LEISURE_SPORTS_CENTRE),
        ("leikkimaa", Categories.LEISURE_PLAYGROUND, Categories.LEISURE_PLAYGROUND),
        ("laboratorio", None, Categories.MEDICAL_LABORATORY),
        ("minigolf", None, Categories.LEISURE_MINIATURE_GOLF),
        ("hohtogolf", None, Categories.LEISURE_MINIATURE_GOLF),
        ("jooga", None, Categories.GYM),
        ("yoga", None, Categories.GYM),
        ("ryhmäliikunta", None, Categories.LEISURE_SPORTS_HALL),
        ("arboretum", None, Categories.LEISURE_GARDEN),
        ("puu-vallila", None, Categories.PLACE_NEIGHBOURHOOD),
        ("puu-käpylä", None, Categories.PLACE_NEIGHBOURHOOD),
        ("nolla-mök", None, Categories.TOURISM_CHALET),
        ("nollamök", None, Categories.TOURISM_CHALET),
        ("pumptrack", None, Categories.LEISURE_TRACK),
        ("bmx-rata", None, Categories.LEISURE_TRACK),
        ("lastauslaituri", Categories.LOADING_DOCK, Categories.LOADING_DOCK),
        ("lastausalue", Categories.LOADING_DOCK, Categories.LOADING_DOCK),
        ("lastbrygga", Categories.LOADING_DOCK, Categories.LOADING_DOCK),
        ("loading dock", Categories.LOADING_DOCK, Categories.LOADING_DOCK),
        # Generic-coverage nouns (2026-10): rescue-only, so tabled units keep
        # their filing. Each verified against filed units before adding.
        ("trampoliini", Categories.LEISURE_TRAMPOLINE_PARK, None),
        ("seikkailupuisto", Categories.LEISURE_SPORTS_CENTRE, None),
        ("pulkkamäki", Categories.LEISURE_PLAYGROUND, None),
        ("ulkoilumaja", Categories.SHELTER, None),
        ("hiihtomaja", Categories.SHELTER, None),
        ("moottorihalli", Categories.COMMUNITY_CENTRE, None),
        ("mopohalli", Categories.COMMUNITY_CENTRE, None),
        ("eteläsatama", Categories.FERRY_TERMINAL, None),
        ("valtuusto", Categories.OFFICE_GOVERNMENT, None),
        ("kaupunginhallitus", Categories.OFFICE_GOVERNMENT, None),
        ("kulttuuripaja", Categories.COMMUNITY_CENTRE, None),
        ("kansalaistoiminta", Categories.COMMUNITY_CENTRE, None),
        ("yleisökassa", Categories.PAYMENT_CENTRE, None),
        ("matkatavarasäilytys", Categories.LUGGAGE_LOCKER, None),
        ("venetaksi", Categories.TOURISM_BOAT_TOURS, None),
        ("taxi boat", Categories.TOURISM_BOAT_TOURS, None),
        ("monistamo", Categories.SHOP_COPYSHOP, None),
        ("banditila", Categories.AMENITY_STUDIO, None),
        ("musiikkistudio", Categories.AMENITY_STUDIO, None),
        ("silmälasi", Categories.SHOP_OPTICIAN, None),
        ("lasistudio", Categories.ARTS_CENTRE, None),
        ("keramiikka", Categories.SHOP_POTTERY, None),
        ("askartelupaja", Categories.ARTS_CENTRE, None),
        ("pitopalvelu", Categories.CRAFT_CATERER, None),
        ("catering", Categories.CRAFT_CATERER, None),
        ("energianeuvonta", Categories.OFFICE_CONSULTING, None),
        ("energiatori", Categories.OFFICE_CONSULTING, None),
        ("puolustusvoimat", Categories.OFFICE_GOVERNMENT, None),
        ("ympäristökeskus", Categories.OFFICE_GOVERNMENT, None),
        ("ympäristöterveys", Categories.OFFICE_GOVERNMENT, None),
        ("apuvälinemyymälä", Categories.SHOP_MEDICAL_SUPPLY, None),
        ("sirkuskoulu", Categories.TRAINING, None),
        ("musiikkiopisto", Categories.MUSIC_SCHOOL, None),
        ("koirakäymälä", Categories.DOG_TOILET, None),
        ("voimalaitos", Categories.POWER_PLANT, None),
        ("kuntoutuskeskus", Categories.REHABILITATION, None),
        ("ravitsemusterapia", Categories.NUTRITIONIST, None),
        ("metsäkeskus", Categories.OFFICE_GOVERNMENT, None),
        ("exit room", Categories.LEISURE_ESCAPE_GAME, None),
        ("leo's", Categories.LEISURE_PLAYGROUND, None),
        ("katsastus", Categories.VEHICLE_INSPECTION, None),
        ("pakastus", Categories.SHOP_STORAGE_RENTAL, None),
        ("tukisuhde", Categories.SOCIAL_FACILITY_OUTREACH, None),
        ("tiny wonders", Categories.KINDERGARTEN, None),
    )
    # Filtered views, order-preserving: rescue serves untabled units,
    # NAME_CATEGORIES refines tabled ones.
    RESCUE_SUBSTRINGS = tuple((s, r) for s, r, _f in NOUN_TABLE if r is not None)
    NAME_CATEGORIES = tuple((s, f) for s, _r, f in NOUN_TABLE if f is not None)

    def _is_mall(self, text):
        # Anchored names and comma-free suffixes (Myllypuron Ostari); comma
        # tenants inside (Partioaitta Iso Omena) must not inherit shop=mall.
        return re.match(self.MALL_START_RE, text) is not None or (
            re.search(self.MALL_ANY_RE, text) and "," not in text and "kauppakeskus" not in text
        )

    # Mainland districts ending in -saari (cf. Vuosaari, Lauttasaari,
    # Kulosaari) are not islands.
    ISLAND_DISTRICTS = (
        "vuosaari",
        "lauttasaari",
        "jätkäsaari",
        "jätkasaari",
        "kulosaari",
        "verkkosaari",
        "sompasaari",
        "salmisaari",
        "hernesaari",
        "siltasaari",
        "lehtisaari",
        "kuusisaari",
    )

    def _island_address(self, unit):
        # Island-name corroboration from the record address: named islands
        # carry their island name in street_address (cf. Kotiluoto).
        street = unit.get("street_address") or {}
        if isinstance(street, dict):
            for key in ("fi", "sv", "en"):
                addr = str(street.get(key) or "").lower()
                if re.search(r"(saari|saaret|luoto|luodot|holma|holme|holmar|öar|island|ö)\b", addr):
                    return True
        return False

    def _rescue_special_name(self, item, text):
        if re.search(self.UFF_RE, text):
            # Bare "uff" also matches "Minibuffet", hence word-boundary.
            apply_category(Categories.SHOP_SECOND_HAND, item)
        elif self._is_mall(text):
            # Anchored mall names and comma-free suffixes (cf. Myllypuron Ostari).
            apply_category(Categories.SHOP_MALL, item)
        elif re.search(self.PAR3_RE, text):
            # Par-3 short courses; bare "par3" also matches spar30 etc.
            apply_category(Categories.LEISURE_GOLF_COURSE, item)
        elif kind := self._city_info_kind(text):
            # Tourist/city info with no tabled node (cf. HSL Vantaa-info
            # points filed only under untabled service nodes).
            apply_category(Categories.TOURISM_INFORMATION, item)
            item["extras"]["information"] = kind
        elif "pumptrack" in text or "bmx" in text:
            # Ride tracks, not ball fields; no BMX value in Sport.
            apply_category(Categories.LEISURE_TRACK, item)
            add_sport(Sport.CYCLING, item)
        else:
            return False
        self._stat("category/rescued")
        return True

    def _rescue_desc_venue(self, item, unit):
        # Description evidence for activity venues filed under the catch-all
        # 2246 node, whose names say nothing (cf. Sugoi, EXITE, Fööni).
        # Gated on 2246: the same nouns elsewhere (cafés showing matches,
        # hotels near golf courses) must not mistag. Tight compounds only.
        if 2246 not in set(self._service_ids(unit)):
            return False
        description = unit.get("description") or {}
        desc = str(description.get("fi") or "").strip().lower() if isinstance(description, dict) else ""
        if not desc:
            return False
        sports = []
        if (
            "pelihalli" in desc
            or "videopeli" in desc
            or "arcade" in desc
            or "vr-areena" in desc
            or "vr areena" in desc
            or "virtual reality" in desc
        ):
            # VR first: OLiO's escape rooms run inside the VR arena, so both
            # arcade nouns and VR nouns precede the pakohuone branch below.
            apply_category(Categories.AMUSEMENT_ARCADE, item)
        elif "pakohuone" in desc or "escape room" in desc:
            apply_category(Categories.LEISURE_ESCAPE_GAME, item)
        elif "kirveenheitto" in desc or "axe throwing" in desc:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            sports.append(Sport.AXE_THROWING)
        elif "tuulitunneli" in desc or "vapaalentotunneli" in desc or "wind tunnel" in desc:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
        elif "lentosimulaattori" in desc or "flight simulator" in desc:
            apply_category(Categories.TOURISM_ATTRACTION, item)
        elif "golfsimulaattori" in desc or "golf-simulaattori" in desc or "trackman" in desc:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            sports.append(Sport.GOLF)
        elif "padel" in desc:
            apply_category(Categories.LEISURE_SPORTS_HALL, item)
            sports.append(Sport.PADEL)
        elif self._rescue_desc_leisure(item, desc, sports):
            # Racket halls, studios, simulators, trampolines and rentals.
            pass
        else:
            return False
        if sports:
            add_sport(sports, item)
        return True

    def _rescue_desc_leisure(self, item, desc, sports):
        # Second half of the 2246 description evidence (split out for
        # flake8 max-complexity); branch order with the head matters.
        if "tenniskenttä" in desc or "sulkapallokenttä" in desc:
            # Racket halls (cf. Outshine Center): tag each sport present.
            apply_category(Categories.LEISURE_SPORTS_HALL, item)
            if "tennis" in desc:
                sports.append(Sport.TENNIS)
            if "sulkapallo" in desc or "badminton" in desc:
                sports.append(Sport.BADMINTON)
        elif "photobooth" in desc:
            # Photo-booth studios (cf. Muikku Photo).
            apply_category(Categories.AMENITY_STUDIO, item)
        elif "golfata" in desc and "simulaattori" in desc:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            sports.append(Sport.GOLF)
        elif "simulaattori" in desc:
            # Simulator venues with no more specific mapping (cf. Takeoff
            # flight simulators): attractions, not generic.
            apply_category(Categories.TOURISM_ATTRACTION, item)
        elif "trampoliin" in desc:
            # Stem covers trampoliini/trampoliineilla/trampoliinipuisto.
            apply_category(Categories.LEISURE_TRAMPOLINE_PARK, item)
        elif "jalkapallo" in desc:
            # Sports-entertainment concepts (cf. Reaktion Games); bars merely
            # showing matches never file under 2246.
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            sports.append(Sport.SOCCER)
        elif (
            any(
                word in desc
                for word in ("sup-laudat", "sup laudat", "suppailu", "kajak", "kanootti", "polkuvene", "soutuvene")
            )
            and "vuokra" in desc
        ):
            # Rental rowboats, SUP boards and kayaks (cf. Laguuni).
            apply_category(Categories.AMENITY_BOAT_RENTAL, item)
        else:
            return False
        return True

    def _rescue_sport_venue(self, item, unit, text):
        # Sport-carrying name rescues for untabled units: the sport noun is
        # certain, so both tags apply together (cf. the pumptrack block
        # above). Also hosts the transport-node-gated ferry/airport rules,
        # which need service_ids and cannot live in NOUN_TABLE.
        if ("jooga" in text or "yoga" in text) and "festiva" not in text:
            # Yoga studios; festival names are events, not venues.
            apply_category(Categories.GYM, item)
            add_sport(Sport.YOGA, item)
        elif "pilate" in text:
            # Stem covers pilates/pilatesta.
            apply_category(Categories.GYM, item)
            add_sport(Sport.PILATES, item)
        elif "ampumahiihto" in text:
            apply_category(Categories.LEISURE_PITCH, item)
            add_sport(Sport.BIATHLON, item)
        elif "ampumarata" in text:
            if any(word in text for word in ("sisä", "sisa", "indoor")):
                # Indoor ranges are halls per the node-628 table row.
                apply_category(Categories.LEISURE_SPORTS_HALL, item)
            else:
                apply_category(Categories.LEISURE_PITCH, item)
            add_sport(Sport.SHOOTING, item)
        elif "hiihtokeskus" in text or "hiihtomaa" in text:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.CROSS_COUNTRY_SKIING, item)
        elif "shakkilauta" in text or "shakkilaudat" in text:
            apply_category(Categories.LEISURE_PITCH, item)
            add_sport(Sport.CHESS, item)
        elif "kiintorasti" in text:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.ORIENTEERING, item)
        elif "kiipeilyhalli" in text or "kiipeilyareena" in text:
            # Indoor walls only; outdoor crags (ulkokiipeilypaikka) stay out.
            apply_category(Categories.LEISURE_SPORTS_HALL, item)
            add_sport(Sport.CLIMBING, item)
        elif "padel" in text:
            apply_category(Categories.LEISURE_SPORTS_HALL, item)
            add_sport(Sport.PADEL, item)
        elif "parkour" in text:
            # Indoor academies and halls (cf. Parkour Akatemia); outdoor
            # spots stay with their filing.
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.PARKOUR, item)
        elif "arena center" in text:
            # Floorball-hall chain (cf. Ruskeasuo/Hakaniemi descs, both
            # salibandy-first); tabled halls keep their filing.
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.FLOORBALL, item)
        elif any(word in text for word in ("wake park", "wakeboard", "wakeskate")):
            # Cable wake parks (cf. Ridenjoy Wake Park); bare "wake" also
            # matches cafés and wake-up event names, so compounds only.
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.WAKEBOARDING, item)
        elif "laskettelurinne" in text or "laskettelukeskus" in text:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.SKIING, item)
        elif (
            512 in set(self._service_ids(unit))
            and ("terminaali" in text or ("lentoasema" in text and "rautatieasema" not in text))
            and "bussiterminaali" not in text
            and "bussiasema" not in text
        ):
            # Passenger transport filed as generic traffic (cf.
            # Länsiterminaali 2, Helsinki-Vantaan lentoasema; Eteläsatama
            # arrives via the NOUN_TABLE row instead).
            # Bus terminals share the noun but are not ferry terminals.
            # SIXT/Avis counters, the Vesibussi route, the airport railway
            # station and Tulli customs points share node 512 but not the
            # nouns, so they fall through untouched.
            if "lentoasema" in text:
                apply_category(Categories.AERODROME, item)
            else:
                apply_category(Categories.FERRY_TERMINAL, item)
        else:
            return False
        return True

    def _apply_name_rescue(self, item, unit):
        # Fallback nouns for untabled units (talkoolaituri, unit 60892).
        name = unit.get("name") or {}
        text = self._refine_text(unit) if isinstance(name, dict) else ""
        if self._rescue_special_name(item, text):
            return
        for substring, rescued in self.RESCUE_SUBSTRINGS:
            if substring in text:
                apply_category(rescued, item)
                self._stat("category/rescued")
                return
        if re.search(r"(^kukka\b|\bkukka$)", text):
            # "Kukka" alone also names hills; only bare shop usages.
            apply_category(Categories.SHOP_FLORIST, item)
        elif re.search(r"\bsixt\b", text):
            # "Sixten" is a name, SIXT the car-rental brand.
            apply_category(Categories.CAR_RENTAL, item)
        elif re.search(r"\bsuutari\b", text):
            # "Suutarila" is a place, not a cobbler.
            apply_category(Categories.SHOP_SHOE_REPAIR, item)
        elif (
            re.search(r"(saari|saaret|luoto|luodot|holma|holme|holmar|öar|island)\b", text)
            and not any(word in text for word in ("kauppakeskus", "outlet", "shop", "myymälä"))
            and not any(word in text for word in self.ISLAND_DISTRICTS)
            and (
                re.search(r"(saari|luoto|holma|holme|ö)\s*[).!]*$", text.strip())
                or "saaristo" in text
                or self._island_address(unit)
            )
        ):
            # Named islands under green-area nodes. Shops with island words
            # (Kauppakeskus Saari) and mainland -saari districts (Vuosaari)
            # are excluded above; green-area-only units drop earlier.
            apply_category(Categories.PLACE_ISLAND, item)
        elif "martial arts" in text:
            apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            add_sport(Sport.MARTIAL_ARTS, item)
        elif "outdoor" in text and "gym" not in text:
            if re.search(r"(climb|klättr|kiipeil)", text):
                # Climbing walls/parks are venues, not outdoor-gear shops
                # (cf. Myyrmäen ulkokiipeilypaikka, unit 75230).
                return
            apply_category(Categories.SHOP_OUTDOOR, item)
        elif self._rescue_sport_venue(item, unit, text) or self._rescue_desc_venue(item, unit):
            # Sport-carrying name rescues (yoga studios, shooting ranges),
            # else description evidence for 2246-filed activity venues.
            # Short-circuit: descs consulted only when names fail.
            pass
        elif set(self._service_ids(unit)) <= {739, 750}:
            # Generic shops with no trade filing (cf. Soma Shop).
            apply_category(Categories.GENERIC_SHOP, item)
        else:
            return
        self._stat("category/rescued")

    def _is_water_post(self, unit):
        name = unit.get("name") or {}
        if not isinstance(name, dict):
            return False
        return str(name.get("fi") or "").strip().lower().startswith("vesiposti")

    EDU_CATEGORIES = {
        Categories.SCHOOL,
        Categories.KINDERGARTEN,
        Categories.LIBRARY,
        Categories.COLLEGE,
        Categories.UNIVERSITY,
    }
    FOOD_CATEGORIES = {Categories.RESTAURANT, Categories.CAFE, Categories.BAR, Categories.CANTEEN}
    FOOD_NOUNS = ("ravintola", "kahvila", "baari", "pub", "pizzeria", "bistro", "ruokala")
    CITY_OPERATORS = {
        "Helsingin kaupunki": "Helsinki",
        "Espoon kaupunki": "Espoo",
        "Vantaan kaupunki": "Vantaa",
        "Kauniaisten kaupunki": "Kauniainen",
        "Kirkkonummi": "Kirkkonummi",
        "Inkoo": "Inkoo",
        "Siuntio": "Siuntio",
        "Lohja": "Lohja",
        "Raasepori": "Raasepori",
        "Vihti": "Vihti",
    }
    # (keyword, brand, QID, match): word needs both boundaries (cf. Minibuffet
    # vs uff), phrase matches multi-word names verbatim, prefix allows
    # Finnish inflection at the end (cf. Pelastusarmeijan kirpputori).
    CHAIN_BRANDS = (
        ("norlandia", "Norlandia", "Q137463892", "prefix"),
        ("pilke", "Pilke", "Q25451570", "prefix"),
        ("pelastusarmeija", "Pelastusarmeija", "Q120647975", "prefix"),
        ("uff", "UFF", "Q11899315", "word"),
        ("kierrätyskeskus", "Pääkaupunkiseudun Kierrätyskeskus", "Q20920687", "prefix"),
        ("spr kontti", "SPR Kontti", "Q409603", "phrase"),
        ("aimo park", "Aimo Park", "Q126728228", "phrase"),
        ("punaisen ristin kontti", "SPR Kontti", "Q409603", "phrase"),
        ("terveystalo", "Terveystalo", "Q11897034", "word"),
        ("finnkino", "Finnkino", "Q5450883", "prefix"),
        ("scandic", "Scandic", "Q129391", "start"),
    )

    def _match_brand_keyword(self, keyword, match, text):
        if match == "word":
            return re.search(r"\b" + re.escape(keyword) + r"\b", text)
        if match == "phrase":
            # Multi-word names match as phrases (cf. SPR Kontti).
            return keyword in text
        if match == "start":
            # Chain-first names only ("Scandic Meilahti", unit 54709):
            # "Marski by Scandic" (unit 20877) and parking at Scandic
            # hotels (units 67632/67692) must not brand as Scandic.
            # Leading whitespace is the empty organizer (cf. _apply_brand).
            return re.match(r"\s*" + re.escape(keyword), text)
        # Bare substring matched Minibuffet-style lookalikes before.
        return re.search(r"\b" + re.escape(keyword) + r"\w*", text)

    # ---- Category refinement for tabled units: name nouns beat feed
    # ---- filing, then subtags; unresolvable stays uncategorised.
    def _school_category(self, text):
        match = re.search(r"(päiväkoti|lukio|opisto|koulu)\b", text)
        if not match:
            return None
        return {"päiväkoti": Categories.KINDERGARTEN, "opisto": Categories.COLLEGE}.get(
            match.group(1), Categories.SCHOOL
        )

    def _has_no_premises(self, category, text):
        if category not in (
            Categories.SOCIAL_FACILITY,
            Categories.OFFICE_GOVERNMENT,
            Categories.COMMUNITY_CENTRE,
            Categories.CLINIC,
            Categories.PLACE_OF_WORSHIP,
        ):
            return False
        if "puhelinpalvelu" in text or text.rstrip().endswith("yhteystiedot"):
            return True
        if any(word in text for word in ("liikkuva", "etsivä", "työryhmä")):
            return True
        if category == Categories.COMMUNITY_CENTRE and "kirjasto" in text:
            # The library has its own unit; this is its program.
            return True
        if category == Categories.OFFICE_GOVERNMENT and "opetuspaikka" in text:
            return True
        if category == Categories.PLACE_OF_WORSHIP and any(word in text for word in ("torni", "krypta", "linnoitus")):
            return True
        return False

    # Named node groups used by refine rules, so the rules read as filings
    # rather than magic ids (cf. WELFARE_NODES, REPAIR_NODE_IDS).
    BILLING_NODES = frozenset({93, 301})
    RENTAL_SAUNA_NODES = frozenset({155, 264, 511})
    ADULT_GUIDANCE_NODES = frozenset({2187, 2188})

    # Hospital wards and receptions are departments, not hospitals
    # ("Geropsykiatrian vastaanotto, Pasila", unit 76614). Mobile units
    # keep the hospital (standing decision); bare institution names keep it
    # too ("Naistenklinikka" is a hospital building, "Tammisairaala" 77573).
    HOSPITAL_NODES = frozenset({1009, 1010, 1012})
    HOSPITAL_DEPT_RE = re.compile(
        r"(osasto|vastaanot|poliklinik|klinik|yksikk|röntgen|rontgen|laboratorio|leikkaus|terapi|terapeut|neuvon|diabetes|synnyt|seulon|fysioterapi|fysiologia|puheterapi|kuntoutus|päivyst)"
    )
    HOSPITAL_MOBILE_RE = re.compile(r"(liikkuva|etsivä|kiertävä)")
    CLINICAL_CATEGORIES = frozenset(
        {
            Categories.CLINIC,
            Categories.CLINIC_URGENT,
            Categories.DOCTOR_GP,
            Categories.DENTIST,
            Categories.NURSE_CLINIC,
            Categories.MEDICAL_LABORATORY,
            Categories.MEDICAL_IMAGING,
            Categories.SPEECH_THERAPIST,
            Categories.PHYSIOTHERAPIST,
            Categories.PODIATRIST,
        }
    )

    def _refine_special_category(self, category, text, unit, winner):
        # One-off filing corrections; None falls through to the noun tables.
        if winner in self.BILLING_NODES and self._is_water_post(unit):
            # Water posts filed with billing offices are drinking-water taps.
            return Categories.DRINKING_WATER
        if category == Categories.RECYCLING and "hallinto" in text:
            # Company HQ filed as a recycling centre (cf. Kierrätyskeskus Oy).
            return Categories.OFFICE_COMPANY
        if category == Categories.TOURISM_ARTWORK and (
            "muistomerkki" in text
            or "muistolaatta" in text
            or "patsas" in text
            or "memorial" in text
            or "minnesmärke" in text
            or "plaque" in text
            or "statue" in text
        ):
            # Named memorials filed as public art (cf. Talvisodan
            # kansallinen muistomerkki, unit 55958; plaques like Tove
            # Janssonin muistolaatta 23494 and statues like Mannerheimin
            # ratsastajapatsas 23142 carry no muistomerkki stem).
            return Categories.HISTORIC_MEMORIAL
        if "henkilöstöravintola" in text:
            # Staff canteens are canteens even when co-filed as restaurants
            # (unit 77540 under generic Ravintolat).
            return Categories.CANTEEN
        if winner == 2190 and "terveys" in text and re.search(r"(hyvinvointikeskus|terveyskeskus|perhekeskus)", text):
            # Genuine health centres filed under the wellness-centre service
            # node (Myllypuro 61667, Kalasatama 54491, both terveys- ja
            # hyvinvointikeskus); pure wellness names without terveys and
            # eco-stores like Ruohonjuuri keep their filing.
            return Categories.CLINIC
        if winner == 688 and "laituri" in text and "talkoolaituri" not in text:
            # Swimming piers filed as beaches (Gälisnäsin uimalaituri 79589).
            # Tool libraries borrow the same noun (talkoolaituri); they keep
            # their rescue category.
            return Categories.MAN_MADE_PIER
        if re.search(r"\w+museo$", text) and category in (
            Categories.RESTAURANT,
            Categories.CAFE,
            Categories.BAR,
            Categories.HOTEL,
        ):
            # Museums about food are still museums (cf. Hotelli- ja
            # ravintolamuseo); a restaurant merely named "Museo" keeps food.
            return Categories.MUSEUM
        if self._is_mall(text):
            # Real malls filed under events/restaurant/hotel nodes
            # (cf. Iso Omena with 750+2173) or suffixed without a comma
            # (cf. Myllypuron Ostari); comma tenants never match.
            return Categories.SHOP_MALL
        if category in (Categories.CAFE, Categories.RESTAURANT) and re.search(r"\bbar\b|\bbaari\b", text):
            # "Kahvila Bar" is a bar; NAME_CATEGORIES would keep CAFE.
            return Categories.BAR
        if "jokamiesgolf" in text or re.search(self.PAR3_RE, text):
            # Short/pay-and-play courses filed under sports nodes.
            return Categories.LEISURE_GOLF_COURSE
        return None

    def _hospital_department_category(self, category, matched, unit, text):
        if self.HOSPITAL_MOBILE_RE.search(text):
            return category
        if "päivyst" in text:
            # Emergency departments read as urgent care (unit 70479).
            return Categories.CLINIC_URGENT
        if not self.HOSPITAL_DEPT_RE.search(text):
            return category
        name = unit.get("name") or {}
        fi = str(name.get("fi") or "") if isinstance(name, dict) else ""
        # A trailing hospital head does not count as department evidence on
        # its own ("Naistenklinikka" is the hospital itself); anything
        # before it does ("Kliininen neurofysiologia, Raaseporin sairaala").
        if not self.HOSPITAL_DEPT_RE.search(re.sub(r"(sairaala|klinikka)\s*$", "", fi, flags=re.IGNORECASE)):
            # Bare institution names are the hospital itself.
            return category
        for rule in sorted(matched, key=lambda r: self.rule_precedence[r]):
            cofiled, _ = self.SERVICE_NODES[rule]
            if cofiled in self.CLINICAL_CATEGORIES:
                # Imaging/lab co-filing beats the hospital row
                # ("Kliininen neurofysiologia, Raaseporin sairaala", 68400).
                return cofiled
        return Categories.CLINIC

    def _refine_category(self, category, matched, unit):
        # Facility nouns in names beat feed filing, in every language.
        text = self._refine_text(unit)
        winner = self._earliest(matched)
        if special := self._refine_special_category(category, text, unit, winner):
            return special
        if category == Categories.HOSPITAL and winner in self.HOSPITAL_NODES:
            return self._hospital_department_category(category, matched, unit, text)
        for substring, refined in self.NAME_CATEGORIES:
            if substring in text:
                if substring in ("kirjasto", "bibliotek", "library") and category != Categories.TOURISM_ATTRACTION:
                    # Library nouns only correct misfiled sights (Vallilan
                    # kirjasto, unit 80323); program venues (80660) and parks
                    # named after libraries (Kirjastonpuisto) keep filing.
                    continue
                if substring == "laboratorio" and category == Categories.UNIVERSITY:
                    # University labs are research offices, not medical labs.
                    continue
                return refined
        if re.search(self.UFF_RE, text):
            # UFF chain stores filed under vague commercial nodes.
            return Categories.SHOP_SECOND_HAND
        if text.startswith(("hotelli", "hotel")) and category == Categories.LEISURE_NATURE_RESERVE:
            # A hotel in a reserve area is still a hotel.
            return Categories.HOTEL
        if "asukaspuisto" in text and category == Categories.SCHOOL:
            # Residents' parks filed under education nodes.
            return Categories.LEISURE_PLAYGROUND
        if category in (Categories.OFFICE_GOVERNMENT, Categories.THEATRE, Categories.COLLEGE):
            # School units filed under office/theatre nodes (cf. Outamon koulu).
            if school := self._school_category(text):
                return school
        desc = unit.get("description") or {}
        desc_text = str(desc.get("fi") or "").strip().lower() if isinstance(desc, dict) else ""
        return self._refine_place(category, matched, text, desc_text, unit)

    def _clinic_category(self, category, text):
        if category == Categories.CLINIC:
            if "vertaistuki" in text:
                # Peer-support groups are not clinics.
                return Categories.SOCIAL_FACILITY
            if text.rstrip().endswith("palvelun järjestämispaikka"):
                # Hired venues, not the service filed there.
                return Categories.COMMUNITY_CENTRE
        return None

    def _park_category(self, category, text, unit=None):
        # Tails checked per language: the blob ends in English, hiding a fi
        # -puisto ending (Roineenpuisto, unit 64840).
        tails = [text.rstrip()]
        if unit is not None:
            fi, sv, en = self._names_lower(unit)
            tails = [fi.rstrip(), sv.rstrip(), en.rstrip(), text.rstrip()]
        if any(
            t.endswith("tori") and not t.endswith(("konttori", "toimisto", "varasto")) for t in tails
        ) and category in (Categories.TOURISM_ATTRACTION, Categories.MARKETPLACE):
            # Market squares filed as sights (cf. Hakaniementori); a tori
            # is a square first, market function or not (cf. Töölöntori,
            # unit 34753, filed straight as marketplace).
            return Categories.TOURISM_ATTRACTION_SQUARE
        if any(t.endswith(("puisto", "parken", "park")) or re.search(r"\bpark$", t) for t in tails) and category in (
            Categories.TOURISM_ATTRACTION,
            Categories.TOURISM_ARTWORK,
            Categories.COMMUNITY_CENTRE,
        ):
            # Parks filed as sights, art or community venues (cf. Kalasatamanpuisto).
            # Amusement parks are attractions, not parks (cf. Linnanmäki).
            if "amusement" in text:
                return None
            return Categories.LEISURE_PARK
        # A pitch at a beach stays a pitch (Rantafutis, unit 41120): fi decides
        # when present; sv/en tails count only without a fi name.
        fi_has_name = bool(tails[0].strip()) if tails else False
        beach_tails = [tails[0]] if fi_has_name else tails
        if any(t.endswith("uimaranta") for t in beach_tails) or any(
            re.search(r"\b(badstrand|badstranden|beach)\s*$", t, re.IGNORECASE) for t in beach_tails
        ):
            # Swedish/en tails need a separate word: one-word Sandstrand names
            # the shore (Hietsun Paviljonki), and hotel Strand is never a beach.
            if category != Categories.NATURAL_BEACH:
                return Categories.NATURAL_BEACH
        return None

    def _activity_category(self, category, text, desc=""):
        if category == Categories.LEISURE_FITNESS_STATION and "lähiliikuntapaikka" in text:
            if re.search(
                r"(miniareena|ministadion|pallopel|pallokentt|pelikentt|monitoimikentt)\w*", text + " " + desc
            ):
                # Ball-game arenas are pitches, whatever the gym gear around them.
                return Categories.LEISURE_PITCH
            if re.search(r"(koulu|skol)\w*", text):
                # Schoolyard areas read as playgrounds (Kungsgårdsskolan).
                return Categories.LEISURE_PLAYGROUND
        if category == Categories.LEISURE_FITNESS_STATION and "leikkipuisto" in text:
            # Playgrounds with gym gear are still playgrounds.
            return Categories.LEISURE_PLAYGROUND
        if category == Categories.LEISURE_SPORTS_CENTRE and "jumppa-alue" in text:
            # Park workout areas are fitness stations, not arenas.
            return Categories.LEISURE_FITNESS_STATION
        return None

    def _wellness_category(self, category, text):
        if category != Categories.SAUNA:
            return None
        if re.search(r"(parturi|barber|kampaamo|\bhair\b)", text):
            # Barbers filed as wellness services (cf. Next Century Fashion).
            return Categories.SHOP_HAIRDRESSER
        if any(word in text for word in ("kauneus", "kosmet", "beauty")):
            return Categories.SHOP_BEAUTY
        if "tatu" in text:
            return Categories.SHOP_TATTOO
        if any(word in text for word in ("hieronta", "massage")):
            return Categories.SHOP_MASSAGE
        if "fysio" in text:
            return Categories.PHYSIOTHERAPIST
        if any(word in text for word in ("jooga", "yoga")):
            return Categories.GYM
        if not re.search(
            r"(sauna|löyly|kylpy|uinti|kellumo|bastu|\bspa\b|\bshop\b|kauppa|myymälä|store)",
            text,
        ):
            # 2168 filing with neither sauna evidence nor a trade word owned
            # by a later rule (cf. Pranama Kallio, Hyvinvointitila): a
            # wellness filing without evidence is not a sauna.
            self._stat("category/wellness_generic")
            return Categories.GENERIC_POI
        return None

    def _station_category(self, category, text):
        if category == Categories.TRAIN_STATION and (
            re.search(r"metroasema\s+[a-z]\b", text)
            or any(word in text for word in ("sisäänkäynti", "uloskäynti", "entrance"))
        ):
            # Letter-suffixed metro units are entrances (cf. Matinkylän metroasema C).
            return Categories.RAILWAY_SUBWAY_ENTRANCE
        return None

    # Teaching-unit words shared by the clinic guard and the stay-with-the-
    # institution rule below; one tuple so they cannot drift apart.
    UNIVERSITY_DEPT_WORDS = (
        "laitos",
        "korkeakoulu",
        "tiedekunta",
        "department",
        "school",
        "högskola",
        "kielikeskus",
    )
    # Service desks, not the institution (cf. vahtimestarit).
    UNIVERSITY_SERVICE_DESK_WORDS = (
        "palvelupiste",
        "opiskelijapalvelu",
        "oppimispalvelu",
        "kirjaamo",
        "vahtimestari",
        "noutopiste",
        "hallinto",
        "kulkukortti",
        "starting point",
        "it-palvelu",
    )
    UNIVERSITY_LAB_RE = (
        r"(laboratorio|laboratory|\blab\b|fablab|nanofab|printlab|\bhiit\b|instituutti|institute|"
        r"observatorio|biofilia|design factory|\bstudios?\b|media lab|paja|grafiikka)"
    )
    UNIVERSITY_GUEST_RE = r"(vierastalo|aalto inn|guest ?house)"
    # Individual buildings, not the institution.
    UNIVERSITY_BUILDING_RE = (
        r"(rakennus|talo$|unioninkatu|fabianinkatu|physicum|exactum|chemicum|biomedicum|biokeskus|"
        r"snellmania|athena|minerva|topelia|metsätalo|economicum|korona|infokeskus|tiedekulma|"
        r"silinteri|tornit|dipoli|valimo|lastausalue|ee-rakennus|päärakennus|apollon|artemis|kandidaattikeskus)"
    )

    def _university_category(self, category, text):
        if category != Categories.UNIVERSITY:
            return None
        if any(word in text for word in self.UNIVERSITY_SERVICE_DESK_WORDS):
            return Categories.OFFICE_ADMINISTRATIVE
        if re.search(self.UNIVERSITY_LAB_RE, text):
            return Categories.OFFICE_RESEARCH
        has_dept = any(word in text for word in self.UNIVERSITY_DEPT_WORDS)
        if not has_dept and any(word in text for word in ("terveys", "hammas", "poliklinikka", "klinikka")):
            return Categories.CLINIC
        if re.search(self.UNIVERSITY_GUEST_RE, text):
            return Categories.TOURISM_GUEST_HOUSE
        if "kandidaattikeskus" in text and ("arts" in text or "kauppakorkeakoulu" in text):
            # School-specific service points inside the shared
            # Kandidaattikeskus building (cf. ARTS unit 51092,
            # kauppakorkeakoulu unit 50607); the bare record (unit 46043)
            # is the building itself.
            return Categories.OFFICE_ADMINISTRATIVE
        if has_dept:
            # Teaching and research units stay with the institution.
            return None
        if re.search(self.UNIVERSITY_BUILDING_RE, text):
            # Individual buildings are not the institution; with no
            # building category available they stay generic.
            return False
        return None

    def _civic_category(self, category, text):
        if self._city_info_kind(text):
            # City info desks, not offices (cf. Espoonlahden Espoo-info).
            return Categories.TOURISM_INFORMATION
        if category == Categories.COMMUNITY_CENTRE:
            if any(word in text for word in ("neuvonta", "ohjaamo", "ohjaus", "startti")):
                # Guidance desks, not meeting places.
                return Categories.OFFICE_GOVERNMENT
            if any(word in text for word in ("café", "cafe", "deli")):
                return Categories.CAFE
        if category == Categories.OFFICE_GOVERNMENT and "asukastila" in text:
            return Categories.COMMUNITY_CENTRE
        if category == Categories.SOCIAL_FACILITY and "miepä" in text:
            return Categories.COMMUNITY_CENTRE
        if category == Categories.PLACE_OF_WORSHIP and "seurakuntien talo" in text:
            return Categories.OFFICE_GOVERNMENT
        return None

    def _facility_correction(self, category, matched, text):
        if category == Categories.SAUNA and re.search(r"\bspa\b", text):
            return Categories.SHOP_BEAUTY_SPA
        if category == Categories.SHOP_HEALTH_FOOD:
            if "hammas" in text:
                return Categories.DENTIST
            if "terveyskeskus" in text or "terveysasema" in text:
                return Categories.CLINIC
        if category == Categories.CARAVAN_SITE and (
            "saari" in text or "luoto" in text or "pursiseura" in text or "yacht" in text
        ):
            # Islands and yacht clubs are not caravan sites.
            return None
        if self._has_no_premises(category, text):
            return None
        food = {r for r in matched if self.SERVICE_NODES[r][0] in self.FOOD_CATEGORIES}
        edu = {r for r in matched if self.SERVICE_NODES[r][0] in self.EDU_CATEGORIES}
        if food and edu and text.startswith(self.FOOD_NOUNS):
            # A restaurant inside a university is still a restaurant.
            return self.SERVICE_NODES[self._earliest(food)][0]
        return category

    def _playground_category(self, category, text):
        if category in (Categories.SCHOOL, Categories.KINDERGARTEN) and "leikkipuisto" in text:
            if not re.search(
                r"(päiväkoti|daghem|förskol|esiopet|preschool|kindergarten)",
                text,
            ):
                # Supervised municipal playgrounds (Leikkipuisto Lehdokki):
                # open, free, no placement. Daycare-worded names keep kindergarten.
                return Categories.LEISURE_PLAYGROUND
        return None

    def _church_category(self, category, matched, text):
        # False drops crypts/fortresses to the generic fallback; None passes on.
        if category == Categories.TOURISM_ATTRACTION and any(
            self.SERVICE_NODES[r][0] == Categories.PLACE_OF_WORSHIP for r in matched
        ):
            if self._has_no_premises(Categories.PLACE_OF_WORSHIP, text):
                if "torni" in text:
                    # Visitable towers are sights (cf. Kallion kirkon torni,
                    # 273 steps, guided tower visits) even when church-filed.
                    return Categories.TOURISM_ATTRACTION
                # Crypts and fortresses stay generic.
                return False
            # A church filed as a sight is still a church (cf. Espoon tuomiokirkko).
            return Categories.PLACE_OF_WORSHIP
        return None

    def _swim_category(self, category, unit, text):
        fi_tail, sv_tail, en_tail = self._names_lower(unit)
        swim_tail = any(
            re.search(r"(uimahalli|maauimala|simhall|swimming hall|swimming pool)\s*$", t)
            for t in (fi_tail, sv_tail, en_tail, text)
        )
        gym_word = bool(re.search(r"(kuntosali|liikuntasali|\bgym\b|voimailusali|gymmet)", text))
        if category == Categories.GYM and swim_tail and not gym_word:
            # Co-filed swimming halls keep swimming (Hakunilan uimahalli);
            # gym-only annexes and reverse-ordered pairs stay gym.
            return Categories.LEISURE_SPORTS_CENTRE
        return None

    def _generic_venue_correction(self, category, matched, text):
        # A specific co-filing beats a generic one when the name confirms it:
        # churches over event venues (78853), offices over sights/reserves,
        # non-sauna venues over sauna filings (Teurastamo), shops over
        # advice-desk filings (76939), offices over kindergarten (54059).
        winner = self._earliest(matched)
        cats = {self.SERVICE_NODES[r][0] for r in matched}
        if (
            category == Categories.EVENTS_VENUE
            and Categories.PLACE_OF_WORSHIP in cats
            and re.search(r"(kirkko|kappeli|chapel|church)", text)
        ):
            return Categories.PLACE_OF_WORSHIP
        if (
            category == Categories.TOURISM_ATTRACTION
            and Categories.OFFICE_GOVERNMENT in cats
            and re.search(r"(asiakaspalvelu|virasto|toimisto|service ?point|palvelupiste)", text)
        ):
            return Categories.OFFICE_GOVERNMENT
        if (
            category == Categories.LEISURE_NATURE_RESERVE
            and Categories.OFFICE_GOVERNMENT in cats
            and re.search(r"(ympäristökeskus|ympäristönhoito|ympäristötoimisto|virasto|hallinto)", text)
        ):
            return Categories.OFFICE_GOVERNMENT
        if (
            category == Categories.SAUNA
            and winner in self.RENTAL_SAUNA_NODES
            and Categories.EVENTS_VENUE in cats
            and not re.search(r"(sauna|bastu|bath|kylpy|löyly)", text)
        ):
            # Sauna filing is a venue amenity, not the POI (Teurastamo); genuine
            # saunas name one. Wellness filings (2168) keep their value.
            return Categories.EVENTS_VENUE
        if winner in self.ADULT_GUIDANCE_NODES:
            if re.search(r"(galleria|gallery)", text):
                return Categories.TOURISM_GALLERY
            if re.search(r"(kauppa|shop|myymälä|store)", text):
                return Categories.GENERIC_SHOP
        if (
            category == Categories.KINDERGARTEN
            and Categories.OFFICE_GOVERNMENT in cats
            and re.search(r"(neuvonta|ohjaus|neuvontapalvelu)", text)
        ):
            return Categories.OFFICE_GOVERNMENT
        if Categories.OFFICE_GOVERNMENT in cats and re.search(r"(ryhmäkoti|perhekoti|ryhmäasuminen)", text):
            # Residential group homes (Keravan perheryhmäkoti, unit 76608).
            return Categories.SOCIAL_FACILITY
        return None

    def _refine_place(self, category, matched, text, desc="", unit=None):
        # Helpers return a category, None to pass on, or False to force the
        # generic fallback (only the university and church rules use False).
        # Final None means unmappable.
        if corrected := self._generic_venue_correction(category, matched, text):
            return corrected
        if category == Categories.UNIVERSITY:
            uni = self._university_category(category, text)
            if uni is False:
                # Named buildings: generic, never the institution.
                return None
            if uni is not None:
                return uni
        if activity := self._activity_category(category, text, desc):
            return activity
        if clinic := self._clinic_category(category, text):
            return clinic
        if sauna_trade := self._wellness_desc_category(category, matched, desc):
            return sauna_trade
        if station := self._station_category(category, text):
            return station
        if wellness := self._wellness_category(category, text):
            return wellness
        if civic := self._civic_category(category, text):
            return civic
        if park := self._park_category(category, text, unit):
            return park
        if playground := self._playground_category(category, text):
            return playground
        church = self._church_category(category, matched, text)
        if church is False:
            return None
        if church is not None:
            return church
        if swim := self._swim_category(category, unit, text):
            return swim
        if venue := self._refine_named_venue(category, matched, text, desc):
            return venue
        return self._facility_correction(category, matched, text)

    def _refine_named_venue(self, category, matched, text, desc):
        # Venue-specific overrides for excursion islands whose POI is the
        # venue, not the islet (cf. Suomenlinna fortress, Klippan restaurant
        # island, Särkkä yacht harbour). Bare islets keep PLACE_ISLAND;
        # overnight claims stay out (cf. day-trip-only Porsas), so no
        # camp/picnic inference here.
        if category == Categories.PLACE_ISLAND:
            if "suomenlinna" in text:
                return Categories.TOURISM_ATTRACTION
            if "klippan" in text:
                return Categories.RESTAURANT
            if "särkkä" in text or "sarkka" in text:
                return Categories.MARINA
            if "viljelypalsta" in text:
                # Allotment gardens on islands (cf. Tullisaari): scoped here
                # so parking areas serving allotments keep their tags.
                return Categories.ALLOTMENTS
            if "taxi boat" in text or "venetaksi" in text:
                return Categories.TOURISM_BOAT_TOURS
            return None
        return None

    def _wellness_desc_category(self, category, matched, desc):
        # Trade evidence lives in descriptions for name-opaque 2168 studios
        # (cf. Söndag beauty salon, Saint Katariina hairdresser). Runs before
        # the name-based wellness fallback, which would generic-ify them.
        if category == Categories.SAUNA and matched and self._earliest(matched) == 2168:
            if re.search(r"(kauneus|kosmet|beauty|\bspa\b)", desc):
                return Categories.SHOP_BEAUTY
            if re.search(r"(parturi|kampaamo|barber|hairdresser|frisör|frisor)", desc):
                return Categories.SHOP_HAIRDRESSER
            if re.search(r"(jooga|yoga|pilates)", desc):
                # Yoga/pilates studios (cf. Pranama Kallio/Töölö).
                return Categories.GYM
        return None

    def _apply_info_artwork_track_subtags(self, item, category, fi_name, sv_name, en_name):
        if category == Categories.TOURISM_INFORMATION:
            if "matkailuneuvonta" in fi_name or "tourist information" in en_name:
                item["extras"]["information"] = "office"
            elif "taulu" in fi_name or "opaste" in fi_name:
                # Signboards and guidance points, not staffed offices.
                item["extras"]["information"] = "board"
            else:
                item["extras"]["information"] = "office"
        if category == Categories.TOURISM_ARTWORK:
            if any(word in fi_name for word in ("muraali", "seinämaalaus")):
                item["extras"]["artwork_type"] = "mural"
            elif any(word in fi_name for word in ("graffiti", "katutaide")):
                item["extras"]["artwork_type"] = "graffiti"
        if category == Categories.LEISURE_TRACK and ("pumptrack" in fi_name or "bmx" in fi_name):
            # No BMX value in Sport; CYCLING is the fallback.
            add_sport(Sport.CYCLING, item)

    def _apply_subtags(self, item, unit, category):
        fi_name, sv_name, en_name = self._names_lower(unit)
        if category == Categories.KINDERGARTEN and "ryhmäperhepäiväkoti" in fi_name:
            # Group family daycare (max 12 children, cf. hel.fi family-daycare
            # pages): a distinct Finnish statutory form with no established
            # value (taginfo: kindergarten=group_family_daycare unused as of
            # Oct 2026). kindergarten=* already carries facility-type values,
            # so the Finnish form is named explicitly rather than dropped.
            item["extras"]["kindergarten"] = "group_family_daycare"
        if category == Categories.LEISURE_FITNESS_STATION and ("kuntoportaat" in fi_name or "motionstrappa" in sv_name):
            # Exercise stairs (cf. Helsingin kuntoportaat listings):
            # fitness_station=stairs is on the wiki Key:fitness_station page
            # (645 objects on taginfo, Oct 2026).
            item["extras"]["fitness_station"] = "stairs"
        if category == Categories.LEISURE_PLAYGROUND:
            # Yard restrictions are not feed-verifiable; only commercial
            # playlands (which charge admission) assert access.
            if "leikkimaa" in fi_name:
                item["extras"]["access"] = "customers"
        if category == Categories.LEISURE_GARDEN and "arboretum" in fi_name:
            # Arboretum (cf. Niskalan arboretum, unit 77671 shape):
            # garden:type=arboretum is in use on taginfo (732 objects,
            # Oct 2026), distinct from the botanical-garden values.
            item["extras"]["garden:type"] = "arboretum"
        if category == Categories.SOCIAL_FACILITY and re.search(r"(ryhmäkoti|perhekoti)", fi_name):
            # Named group homes (cf. Keravan perheryhmäkoti, unit 76608).
            item["extras"]["social_facility"] = "group_home"
        if category == Categories.HISTORIC_MEMORIAL:
            # memorial=* subtypes by noun (plaques and statues; generic
            # muistomerkki carries no subtype).
            if "muistolaatta" in fi_name or "plaque" in en_name:
                item["extras"]["memorial"] = "plaque"
            elif "patsas" in fi_name or "statue" in en_name:
                item["extras"]["memorial"] = "statue"
        self._apply_info_artwork_track_subtags(item, category, fi_name, sv_name, en_name)

    def _fixup_pitch_sport(self, item, unit):
        sports = (item.get_tag("sport") or "").split(";")
        if "ice_hockey" not in sports:
            return
        name = unit.get("name") or {}
        pitch_text = self._refine_text(unit) if isinstance(name, dict) else ""
        if Sport.FLOORBALL in self._infer_sports(pitch_text):
            # Floorball rinks filed as ice rinks (cf. Salibandykaukalo).
            sports = [s for s in sports if s != "ice_hockey"]
            if "floorball" not in sports:
                sports.append("floorball")
            item["extras"]["sport"] = ";".join(sorted(s for s in sports if s))

    def _apply_housing_override(self, item, matched):
        if item["extras"].get("social_facility:for") == "senior" and any(m in matched for m in (2160, 2447, 1024)):
            # Also filed under mental-health housing: serves them instead (Kompassi).
            item["extras"]["social_facility:for"] = "mental_health"
            item["extras"]["social_facility"] = "group_home"

    def _has_category(self, item):
        # Any mappable top-level tag counts (cf. landuse=allotments, which
        # carries no amenity).
        return any(item.get_tag(tag) for tag in self.DEDUPE_TAGS)

    # Retail shops filed as repair (JAS Kamerakauppa, unit 72392): the name,
    # not the filing, decides.
    REPAIR_NODE_IDS = frozenset({2299, 2300, 2302, 2298, 2297})
    RETAIL_NAME_WORDS = ("kauppa", "kauppan", "shop", "store", "myymälä", "liike")

    def _apply_category(self, item, unit):
        matched = {
            self.rule_by_service_node[service_id]
            for service_id in self._service_ids(unit)
            if service_id in self.rule_by_service_node
        }
        if matched and self._earliest(matched) in self.REPAIR_NODE_IDS:
            text = self._refine_text(unit)
            if any(word in text for word in self.RETAIL_NAME_WORDS) and not re.search(
                r"(korjaus|huolto|paja|fix|huolletaan)", text
            ):
                # Retail unit filed as repair: drop the filing, let rescue decide.
                matched = {r for r in matched if r not in self.REPAIR_NODE_IDS}
        if not matched:
            self._stat("category/missing")
            self._apply_name_rescue(item, unit)
            if not self._has_category(item):
                # Per docs/CATEGORIES.md: amenity=yes beats a tagless Feature.
                # Unrescuable leftovers (service records without a visitable
                # venue) keep the generic tag, so the pipeline "category not
                # set" residual is expected, not a filing bug.
                apply_category(Categories.GENERIC_POI, item)
                self._stat("category/generic")
            return
        if len(matched) > 1:
            # Earliest-wins; a spike means the tree moved.
            self._stat("category/multi_match")
        winner = self._earliest(matched)
        category, _ = self.SERVICE_NODES[winner]
        category = self._refine_category(category, matched, unit)
        if category is None:
            self._stat("category/skipped")
            apply_category(Categories.GENERIC_POI, item)
            return
        apply_category(category, item)
        if category in (Categories.PARKING, Categories.CAR_SHARING):
            self._apply_parking_capacity(item, unit)
        self._apply_subtags(item, unit, category)
        # Extras ride along from same-category rules only: a ticket machine
        # node on a sports hall must not tag the hall.
        for rule in matched:
            rule_category, extras = self.SERVICE_NODES[rule]
            if rule_category != category:
                continue
            if sport := extras.get("sport"):
                add_sport(sport, item)
            if vending := extras.get("vending"):
                add_vending(vending, item)
            for key, value in extras.items():
                # Plain string extras, e.g. station=subway on metro stations.
                if isinstance(value, str):
                    item["extras"][key] = value
        if category == Categories.LEISURE_PITCH and not item.get_tag("sport"):
            self._apply_pitch_sport(item, unit)
        if category == Categories.LEISURE_PITCH:
            self._fixup_pitch_sport(item, unit)
            if not item.get_tag("sport"):
                # Bare pitch with no inferable sport (new spelling?).
                self._stat("category/pitch_no_sport")
        self._apply_housing_override(item, matched)
