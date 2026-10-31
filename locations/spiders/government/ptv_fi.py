import re
from typing import Callable, Iterable
from urllib.parse import unquote, urlencode

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours, sanitise_day
from locations.items import Feature
from locations.licenses import Licenses

# Finnish Service Catalogue (Palvelutietovaranto, PTV), api.palvelutietovaranto.suomi.fi.
# DVV's CC0 national registry of public-sector services: municipalities, wellbeing
# counties and state agencies describe services, ServiceLocation channels are the
# physical visit points (~38k nationally). Complements helsinki_servicemap_fi
# (metro-only, CC-BY-4.0, different refs): overlap duplicates by design, never
# conflate across spiders, never exclude here because a brand spider exists.
#
# Crawl: id-list pages (?page=N, server default size) then batched detail
# fetches via /list?guids=<comma-joined> (40/call per batch_size, since
# 100-guid URLs trip the urllength middleware). The full-detail area
# endpoint pages at 4/page and is not used. v11 retires 04/2027; v12
# needs an API key.
# PTV latitude/longitude fields are TM35FIN northing/easting, not WGS84.

# Triple returned by every name splitter: (shown name, located venue, official form).
SplitTriple = tuple[str, str | None, str | None]


class PtvFISpider(Spider):
    name = "ptv_fi"
    allowed_domains = ["api.palvelutietovaranto.suomi.fi"]

    dataset_attributes = Licenses.CC0.value

    api_base_url = "https://api.palvelutietovaranto.suomi.fi/api/v11"
    LIST_PATH = "/ServiceChannel/type/ServiceLocation"
    DETAIL_PATH = "/ServiceChannel/list"
    ORG_PATH = "/Organization/list"
    batch_size = 40

    _transformer = Transformer.from_crs(3067, 4326, always_xy=True)

    WEEK_ORDER: tuple[str, ...] = tuple(DAYS)

    # Road furniture, institutional kitchens, bookmobiles and mobile/outreach
    # services are not visitable fixed POIs (cf. service-map excluded subtrees).
    MOBILE_RE = re.compile(r"(etsivä|liikkuva|hoitoauto|palveluauto|auto$)")
    TRACK_RE = re.compile(r"\b(kuntorata|kuntopolku|latu|luontopolku|retkeilyreitti|hiihtolatu|pururata)\b")
    TRACK_WORDS = ("lenkki", "juoksu", "latu", "ladut", "polut", "reitti", "reitit", "reitistö")
    # Track-word rows that still name a visitable venue: sports-hall
    # running straights ("Töölön kisahalli / Juoksusuora"), outdoor gyms
    # ("... / Ulkokuntoilupaikka") and facilities at track-named places
    # ("Reittipuiston lentopallokenttä", "Latupuiston päiväkoti").
    # School-owned tracks ("... koulun hiihtolatu") and park routes
    # ("Keskuspuisto 1 latu") carry no venue head and stay dropped.
    TRACK_VENUE_RE = re.compile(r"(halli|kenttä|stadion|areena|urheilutalo|jäähalli)")
    TRACK_PLACE_RE = re.compile(r"(reittipuisto|latupuisto|latuka\w*)")
    TRACK_FACILITY_RE = re.compile(r"(kenttä|päiväkoti|leikki|koulu|kirjasto|halli|sali)")
    KM_RE = re.compile(r"\d\s*km\b")
    KITCHEN_INFIX = tuple("päiväkoti koulu palvelukeskus hoiva sairaala tuotanto ".split())
    COORD_TAIL_RE = re.compile(r",?\s*(?:[PN]\s*)?\d+\s*°.*$")
    CORE_INSTITUTION_RE = re.compile(r"(koulu|lukio|opisto|päiväkoti|kirjasto|museo|sairaala|neuvola)")
    # Consonant-gradation plurals/genitives normalizing to their singular
    # (kenttä/kentät/kentän, ...). Longest-key-first so compound forms match
    # properly; no leading \b so compounds (pallokentät) match like before.
    GRADATION_MAP = {
        "päiväkotien": "päiväkoti",
        "taideteokset": "taideteos",
        "taideteoksen": "taideteos",
        "paikkojen": "paikka",
        "yhdistykset": "yhdistys",
        "seulonnat": "seulonta",
        "seulonnan": "seulonta",
        "päiväkodit": "päiväkoti",
        "veistokset": "veistos",
        "veistoksen": "veistos",
        "keskuksen": "keskus",
        "tautien": "tauti",
        "yksiköt": "yksikkö",
        "kentät": "kenttä",
        "kentän": "kenttä",
        "rannat": "ranta",
        "rannan": "ranta",
        "paikat": "paikka",
        "paikan": "paikka",
        "taudit": "tauti",
        "radat": "rata",
    }
    GRADATION_RE = re.compile("(" + "|".join(sorted(GRADATION_MAP, key=len, reverse=True)) + r")\b")

    # First match wins; order frozen. Matching is prefix-or-compound
    # ((?:\bkw\w*|\w+kw\b)) so Finnish compounds hit from either side:
    # kaupunginkirjasto and sivuapteekki match, while tori keeps its own
    # rule so auditorio/laboratorio/toimisto never match. päiväkoti
    # precedes koulu so Koulukatu daycares file correctly. Hosted welfare
    # services bypass the table via the nurse guard so school/daycare
    # hosts never outrank them.
    CATEGORY_RULES = (
        (
            "neuvola",
            Categories.CLINIC,
            {"healthcare:speciality": "maternal_and_child_health"},
        ),  # Neuvola (maternity/child-health clinics)
        (
            "päiväkoti|pilke|norlandia|päiväkodin|esiopetus|"
            "perhepäivähoito|perhepäivähoitaja|daghem|dagvård|"
            "ryhmis|dagis|daycare|toddler|preschool|"
            "kindergarten",
            Categories.KINDERGARTEN,
            None,
        ),  # Päiväkoti (daycare)
        ("school", Categories.SCHOOL, None),  # School (schools in English)
        ("oikeusapu", Categories.OFFICE_LAWYER, None),  # Oikeusapu (legal-aid offices)
        ("käräjä|hovioikeus", Categories.COURTHOUSE, None),  # Käräjä (courts)
        ("oikeustiede", Categories.COLLEGE, None),  # Oikeustiede (university law faculties, not courts)
        ("asumisoikeus", Categories.OFFICE_COMPANY, None),  # Asumisoikeus Oy (housing-right companies)
        ("oikeuspsykiatr|oikeuspsykolog", Categories.CLINIC, None),  # Forensic psychiatry units
        ("oikeus", Categories.COURTHOUSE, None),  # Oikeus (courts: supreme, insurance, administrative)
        (
            "kansli|stadshus|kommunhus|suunnittelu",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Kanslia / kansli (admin offices)
        ("psykiatrinen palveluasuminen", Categories.SOCIAL_FACILITY, None),  # Psychiatric housing, not wards
        ("psykiatrinen sairaala|psykiatriasairaala", Categories.HOSPITAL, None),  # Psychiatric hospitals
        (
            "psykiatri|nuorten mielenterveys|nuorten päihde|"
            "nuorten ja aikuisten mielenterveys|nuorten ja aikuisten päihde|tutkimusvastaanotto",
            Categories.CLINIC,
            None,
        ),  # Psykiatri (psychiatry; youth clinical outranks youth centres below)
        ("kohtaamispaikka", Categories.COMMUNITY_CENTRE, None),  # Kohtaamispaikka (meeting places outrank clientele)
        (
            "tukiasunto|tukiasunnot|tuettu asumi|tukiasuminen",
            Categories.ASSISTED_LIVING,
            None,
        ),  # Tukiasunto (supported housing)
        ("mielenterveystyö", Categories.CLINIC, None),  # Mielenterveystyö (mental-health work)
        ("nuorisoasema", Categories.OFFICE_GOVERNMENT, None),  # Nuorisoasema (youth service stations)
        (
            "nuorisotila|nuorisotalo|nuokkari|ungdomslokal|" "ungdomsgård",
            None,
            {"amenity": "youth_centre"},
        ),  # Nuorisotila (youth rooms)
        ("järjestämispaikka", Categories.COMMUNITY_CENTRE, None),  # Järjestämispaikka (activity venues)
        (
            "nuorisokoti|vastaanottokoti",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Nuorisokoti (youth and reception homes house, never clinics or clubs)
        ("nuoriso|nuorten|iltapäivä", Categories.COMMUNITY_CENTRE, None),  # Nuoriso (youth centres)
        ("musiikkiopisto|konservatorio", Categories.MUSIC_SCHOOL, None),  # Musiikkiopisto (music schools)
        (
            "hammashoito|hammashoidon|oikomishoi|" "suun erikoishoi|suun perusterveydenhuolto|" "suun terveydenhuolto",
            Categories.DENTIST,
            None,
        ),  # Hammashoito (dental care)
        ("eläinlääkäri", Categories.VETERINARY, None),  # Eläinlääkäri (veterinarians)
        ("löytöeläi|löytökiss|kissatalo", None, {"amenity": "animal_shelter"}),  # Löytöeläimet (found-animal shelters)
        ("eläinsuojelu", Categories.OFFICE_GOVERNMENT, None),  # Eläinsuojelu (animal-protection desks)
        (
            "ympäristöterveyspalvelu",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Ympäristöterveys (supervision branches, not clinics)
        ("terveyspalvelu|terveystalo|terveyspiste", Categories.CLINIC, None),  # Terveyspalvelu (health services)
        ("sote-aseman lähitori", Categories.SOCIAL_FACILITY, None),  # Sote-aseman lähitorit (service desks)
        ("terveysasema|terveyskeskus|sote-asema", Categories.CLINIC, None),  # Terveysasema (health stations)
        ("fysioterapia", Categories.CLINIC, {"healthcare": "physiotherapist"}),
        (
            "hyvinvointiasema|hyvinvointikeskus|sote-piste|"
            "sotekeskus|sote-keskus|soteasema|poliklinikka|"
            "synnytys|naistentauti|äitiys",
            Categories.CLINIC,
            None,
        ),  # Hyvinvointiasema (wellbeing stations)
        ("puheterapia", Categories.CLINIC, {"healthcare": "speech_therapist"}),  # Puheterapia (speech therapy)
        ("klinikka|klinikat", Categories.CLINIC, None),  # Klinikka (clinics)
        ("näytteenotto|näytteenoton", Categories.SAMPLE_COLLECTION, None),  # Näytteenotto (sampling points)
        ("seulonta", Categories.CLINIC, None),  # Seulonta (health screenings)
        ("laboratorio|lab", Categories.CLINIC, {"healthcare": "laboratory"}),  # Laboratorio (laboratories)
        (
            "kuvantaminen|röntgen|rontgen",
            Categories.CLINIC,
            {"healthcare": "medical_imaging"},
        ),  # Kuvantaminen (imaging)
        ("terapia", Categories.CLINIC, None),  # Terapia (therapy centres)
        ("jalkaterapeutti", Categories.CLINIC, {"healthcare": "podiatrist"}),  # Jalkaterapeutti (podiatrists)
        ("terapeutti|kirurgia|psykoosi|psykologi", Categories.CLINIC, None),  # Terapeutti (therapists)
        (
            "maankäyttö|kaupungin asumispalvelu|" "kunnan asumispalvelu",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Maankäyttö (land-use admin)
        (
            "asumispalveluyksikk|asumisryhmä|asumisyhteisö",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),
        (
            "asumispalvelu|mielenterveyskuntoutujien|" "mielenterveysasiakkaiden",
            Categories.SOCIAL_FACILITY,
            None,
        ),  # Asumispalvelut (housing services)
        (
            "mielenterveys|syömishäiriö|muistikeskus|" "mielialahäiriö|diabeteskeskus",
            Categories.CLINIC,
            None,
        ),  # Mielenterveys (mental health)
        ("diabeteshoitaja", Categories.CLINIC, {"healthcare": "nurse"}),  # Diabeteshoitaja (diabetes nurses)
        ("apteekkimuseo", Categories.MUSEUM, None),  # Apteekkimuseo (pharmacy museums, cf. koulumuseo)
        ("apteekki|apotek", Categories.PHARMACY, None),  # Apteekki (pharmacies)
        ("tarvikejakelu", Categories.SHOP_MEDICAL_SUPPLY, None),  # Tarvikejakelu (supply distribution)
        ("apuväline", Categories.OFFICE_GOVERNMENT, None),  # Apuväline (assistive-device service points)
        ("vastaanottokeskus", Categories.SOCIAL_FACILITY, None),  # Vastaanottokeskus (reception centres)
        ("jäte|jätte", Categories.RECYCLING, None),  # Jäte (waste services)
        (
            "sosiaalipalvelu|elinkeinopalvelu|elinkeinotoimi",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Sosiaalipalvelu (social-service desks)
        ("vastaanotto|vastaanotot", Categories.CLINIC, None),  # Vastaanotto (receptions)
        (
            "beachvolley|beach volley",
            Categories.LEISURE_PITCH,
            {"sport": "beachvolleyball"},
        ),  # Beachvolley (beach volleyball)
        ("volley", Categories.LEISURE_PITCH, {"sport": "volleyball"}),  # Volley (volleyball)
        ("huoltorakennus", None, None),  # Huoltorakennus (service buildings): no precise filing, keep generic
        ("koirauimaranta", Categories.LEISURE_DOG_PARK, None),  # Koirauimaranta (dog beaches)
        ("talviuimari|talviuimaranta", Categories.LEISURE_SWIMMING_AREA, None),  # Talviuimarit (winter swimmers)
        ("uimaranta|uimapaikka", Categories.NATURAL_BEACH, None),  # Uimaranta / uimarannat (beaches)
        (
            "ulkokuntosali|ulkokuntoilu|lähiliikuntapaikka|" "kuntoilupaikka|kuntoilupiste",
            Categories.LEISURE_FITNESS_STATION,
            None,
        ),  # Ulkokuntosali (outdoor gyms)
        ("opastuspiste", Categories.TOURISM_INFORMATION, None),  # Opastuspisteet (info points)
        ("kuntoportaat", Categories.LEISURE_FITNESS_STATION, None),  # Kuntoportaat (fitness stairs)
        ("uimahallin", Categories.GYM, None),  # Uimahallin (gym of a swim hall)
        ("uimahalli", Categories.LEISURE_SPORTS_CENTRE, {"sport": "swimming"}),  # Uimahalli (swimming halls)
        ("uintikeskus", Categories.LEISURE_SPORTS_CENTRE, None),  # Uintikeskus (swimming centres)
        ("kuntosali", Categories.GYM, None),  # Kuntosali (gyms)
        ("uimastadion", Categories.LEISURE_SPORTS_CENTRE, None),  # Uimastadion (swimming stadiums)
        ("uima-allas", Categories.LEISURE_SPORTS_HALL, None),  # Uima-allas (school pools)
        ("maauimala", Categories.LEISURE_SPORTS_CENTRE, {"sport": "swimming"}),  # Maauimala (outdoor pools)
        ("kahluuallas", Categories.LEISURE_SWIMMING_POOL, None),  # Kahluuallas (wading pools)
        (
            "koripallohalli",
            Categories.LEISURE_SPORTS_HALL,
            {"sport": "basketball"},
        ),  # Koripallohalli (basketball halls)
        ("jalkapallohalli", Categories.LEISURE_SPORTS_HALL, {"sport": "soccer"}),  # Jalkapallohalli (football halls)
        ("tennishalli", Categories.LEISURE_SPORTS_HALL, {"sport": "tennis"}),  # Tennishalli (tennis halls)
        (
            "lentopallohalli",
            Categories.LEISURE_SPORTS_HALL,
            {"sport": "volleyball"},
        ),  # Lentopallohalli (volleyball halls)
        ("jalkapallo", Categories.LEISURE_PITCH, {"sport": "soccer"}),  # Jalkapallo (football)
        ("pöytätennis", Categories.LEISURE_PITCH, {"sport": "table_tennis"}),  # Pöytätennis (table tennis)
        ("tenniskenttä", Categories.LEISURE_PITCH, {"sport": "tennis"}),  # Tenniskenttä (tennis courts)
        ("padel", Categories.LEISURE_PITCH, {"sport": "padel"}),  # Padel (padel courts/halls)
        ("koripallo", Categories.LEISURE_PITCH, {"sport": "basketball"}),  # Koripallo (basketball)
        (
            "rantalentopallo",
            Categories.LEISURE_PITCH,
            {"sport": "beachvolleyball"},
        ),  # Rantalentopallo (beach volleyball)
        ("lentopallo", Categories.LEISURE_PITCH, {"sport": "volleyball"}),  # Lentopallo (volleyball)
        ("petanque", Categories.LEISURE_PITCH, {"sport": "petanque"}),  # Petanque (petanque courses)
        ("pesäpallo", Categories.LEISURE_PITCH, {"sport": "pesapallo"}),  # Pesäpallo (Finnish baseball)
        (
            "shakkilauta|shakkilaudat",
            Categories.LEISURE_PITCH,
            {"sport": "chess"},
        ),  # Shakkilauta (outdoor chess boards)
        (
            "liikuntahalli|liikuntakeskus|ulkoilukeskus|" "urheiluhalli",
            Categories.LEISURE_SPORTS_CENTRE,
            None,
        ),  # Liikuntahalli (sports halls)
        ("liikuntasali|liikuntatilat", Categories.LEISURE_SPORTS_HALL, None),  # Liikuntasali (sports halls)
        (
            "tapahtuma-alue|tapahtumalava|tapahtumatalo|" "tapahtumakeskus|tapahtumasali",
            Categories.EVENTS_VENUE,
            None,
        ),  # Tapahtuma-alue (event grounds)
        ("kiipeily", Categories.LEISURE_PITCH, {"sport": "climbing"}),  # Kiipeily (climbing spots)
        ("salibandy", Categories.LEISURE_PITCH, {"sport": "floorball"}),  # Salibandy (floorball)
        ("moottoriurheilu", Categories.LEISURE_PITCH, {"sport": "motor"}),  # Moottoriurheilu (motorsports)
        ("sähly", Categories.LEISURE_PITCH, {"sport": "floorball"}),  # Sähly (floorball)
        ("näyttely|kokoelma", Categories.MUSEUM, None),  # Näyttely (exhibition venues)
        (
            "juhlasali|musiikkisali|monitoimisali|" "valtuustosali",
            Categories.EVENTS_VENUE,
            None,
        ),  # Juhlasali (banquet halls)
        ("lehtilukusali|lehtisali", Categories.LIBRARY, None),  # Lehtilukusali (library reading rooms)
        ("teatterisali", Categories.THEATRE, None),  # Teatterisali (theatre auditoriums, not sports halls)
        ("sali", Categories.LEISURE_SPORTS_HALL, None),  # Sali (halls)
        ("jäähalli", Categories.LEISURE_ICE_RINK, None),  # Jäähalli (ice halls)
        ("keilahalli", Categories.LEISURE_BOWLING_ALLEY, None),  # Keilahalli (bowling halls)
        ("skeittihalli", Categories.LEISURE_SPORTS_CENTRE, {"sport": "skateboard"}),  # Skeittihalli (skate halls)
        ("monitoimihalli", Categories.COMMUNITY_CENTRE, None),  # Monitoimihalli (multipurpose halls)
        ("palloiluhalli|halli", Categories.LEISURE_SPORTS_HALL, None),  # Palloiluhalli (ball-game halls)
        ("auditorio|konserttitalo|kongressitalo", Categories.EVENTS_VENUE, None),  # Auditorio (auditoriums)
        ("parkour", Categories.LEISURE_PITCH, {"sport": "parkour"}),  # Parkour (parkour areas)
        ("streetworkout|street workout", Categories.LEISURE_FITNESS_STATION, None),  # Streetworkout (outdoor gyms)
        ("paini|kamppailu", Categories.LEISURE_SPORTS_HALL, None),  # Paini (wrestling)
        ("bowling", Categories.LEISURE_BOWLING_ALLEY, None),  # Bowling (bowling halls)
        ("minigolf|seikkailugolf|puttiparkki", Categories.LEISURE_MINIATURE_GOLF, None),  # Minigolf (miniature golf)
        ("frisbee|discgolf", Categories.LEISURE_DISC_GOLF_COURSE, None),  # Frisbee / frisbeegolf (disc golf)
        ("golf", Categories.LEISURE_GOLF_COURSE, None),  # Golf (golf courses)
        ("pumptrack|pump track", Categories.LEISURE_TRACK, None),  # Pumptrack (pump tracks)
        ("luistelukenttä|jääkenttä|kaukalo", Categories.LEISURE_ICE_RINK, None),  # Luistelukenttä (skating rinks)
        ("pallokenttä", Categories.LEISURE_PITCH, None),  # Pallokenttä (generic ball fields)
        ("hiekkakenttä", Categories.LEISURE_PITCH, {"surface": "sand"}),  # Hiekkakenttä (sand fields)
        (
            "tekonurmi",
            Categories.LEISURE_PITCH,
            {"sport": "soccer", "surface": "artificial_turf"},
        ),  # Tekonurmi (artificial turf)
        (
            "nurmikenttä",
            Categories.LEISURE_PITCH,
            {"sport": "soccer", "surface": "grass"},
        ),  # Nurmikenttä (grass fields)
        ("yleisurheilukeskus", Categories.LEISURE_SPORTS_CENTRE, {"sport": "athletics"}),
        ("yleisurheilu", Categories.LEISURE_TRACK, None),  # Yleisurheilu (athletics)
        ("urheilukenttä", Categories.LEISURE_PITCH, None),  # Urheilukenttä (sports fields)
        ("kaupunkisoutuvene", Categories.AMENITY_BOAT_RENTAL, None),  # Kaupunkisoutuveneet (borrowable city rowboats)
        ("soutu|melonta|liikuntamylly", Categories.LEISURE_SPORTS_CENTRE, None),  # Soutu (rowing venues)
        ("stadion", Categories.LEISURE_PITCH, None),  # Stadion (stadiums)
        ("skate|skeitti", Categories.LEISURE_PITCH, {"sport": "skateboard"}),  # Skate (skate parks)
        ("leikkipuisto", Categories.LEISURE_PLAYGROUND, None),  # Leikkipuisto (playgrounds)
        ("leikkikerho|leikkikoulu", Categories.KINDERGARTEN, None),  # Leikkikerho (playgroups)
        ("leikkipaikka|leikkikenttä", Categories.LEISURE_PLAYGROUND, None),  # Leikkipaikka (play areas)
        ("leikkivä", None, None),  # Leikkivä titles (artworks like Leikkivät karhut): rescue decides
        ("leikki", Categories.LEISURE_PLAYGROUND, None),  # Leikki (play)
        ("keittokatos", Categories.TOURISM_PICNIC_SITE, None),  # Keittokatos (cooking shelters)
        ("kaupungintalon puisto", Categories.LEISURE_PARK, None),  # Kaupungintalon puisto (city-hall park)
        ("grillipaikka", Categories.TOURISM_PICNIC_SITE, None),  # Grillipaikka (BBQ spots)
        ("koira-aitaus|koirametsä", Categories.LEISURE_DOG_PARK, None),  # Koira-aitaus (dog enclosures)
        ("lippumyymälä|lipunmyynti|lippukassa", None, {"shop": "tickets"}),  # Lippumyymälä (ticket shops)
        ("myymälä", None, {"shop": "yes"}),  # Myymälä (shops)
        ("huvilamuseo", Categories.MUSEUM, None),  # Huvilamuseo (villa museums, cf. koulumuseo)
        ("huvila", None, None),  # Huvila (villas): no precise filing, keep generic
        (
            "kalastuspaikka|kalastuslupa",
            None,
            {"leisure": "fishing"},
        ),  # Kalastuspaikka (fishing spots, incl. at shores/zoo bays)
        ("eläintarha", None, {"tourism": "zoo"}),  # Eläintarha (zoos)
        ("koirapuisto|koiratarha|hundpark", Categories.LEISURE_DOG_PARK, None),  # Koirapuisto (dog parks)
        ("koirakäymälä", None, {"amenity": "dog_toilet"}),  # Koirakäymälä (dog toilets)
        ("pysäköinti", Categories.PARKING, None),  # Pysäköinti (parking)
        ("latauspiste|latausasema", Categories.CHARGING_STATION, None),  # Latauspiste (charging points)
        ("juhannussalko", Categories.TOURISM_ARTWORK, None),  # Juhannussalko (midsummer poles)
        ("henkilöstöravintola", Categories.CANTEEN, None),  # Henkilöstöravintola (staff canteens)
        ("henkilöstöosasto", Categories.OFFICE_GOVERNMENT, None),  # Henkilöstöosasto (HR departments)
        ("kouluravintola|ruokapalvelu", Categories.CANTEEN, None),  # Kouluravintola (school canteens)
        ("ravintola", Categories.RESTAURANT, None),  # Ravintola (restaurants)
        ("ruokala", Categories.CANTEEN, None),  # Ruokala (canteens)
        ("kenttä", Categories.LEISURE_PITCH, None),  # Kenttä (fields)
        ("miniareena", Categories.LEISURE_SPORTS_HALL, None),  # Miniareena (mini arenas)
        ("areena|urheilutalo|liikuntatalo|liikuntapuisto", Categories.LEISURE_SPORTS_CENTRE, None),  # Areena (arenas)
        ("kahvila|kahvio", Categories.CAFE, None),  # Kahvila (cafes)
        ("urheilukeskus|hiihtokeskus", Categories.LEISURE_SPORTS_CENTRE, None),  # Urheilukeskus (sports centres)
        ("monitoimitila", Categories.COMMUNITY_CENTRE, None),  # Monitoimitila (multipurpose rooms)
        ("kirjasto|lainausasema", Categories.LIBRARY, None),  # Kirjasto (libraries)
        ("arkisto", Categories.ARCHIVE, None),  # Arkisto (archives)
        (
            "kansalaisopisto|työväenopisto|opisto|instituutti",
            Categories.COLLEGE,
            None,
        ),  # Kansalaisopisto (civic institutes)
        ("äänitysstudio", Categories.MUSIC_SCHOOL, None),  # Äänitysstudio (recording studios)
        ("akatemia|academy|kampus|keuda|redu", Categories.COLLEGE, None),  # Akatemia (academies)
        ("gymnasi", Categories.SCHOOL, None),  # Gymnasi (gymnasium schools in Swedish, all inflections)
        ("gym|fitness", Categories.GYM, None),  # Gym (gyms in English)
        (
            "lukio|lyseo|peruskoulu|yläaste|ala-aste|" "yhtenäiskoulu",
            Categories.SCHOOL,
            None,
        ),  # Lukio (upper secondary schools)
        ("förskola", Categories.KINDERGARTEN, None),  # Förskola (preschools in Swedish)
        ("skola", Categories.SCHOOL, None),  # Skola (schools in Swedish)
        ("koulutuskeskus", Categories.COLLEGE, None),  # Koulutuskeskus (training centres)
        ("koulutus|koulutukset", Categories.OFFICE_GOVERNMENT, None),  # Koulutus (education services)
        ("uimakoulu", None, None),  # Uimakoulut (swimming lessons): no venue, keep generic
        ("koulumuseo", Categories.MUSEUM, None),  # Koulumuseo (school museums)
        ("koulutoimisto", Categories.OFFICE_GOVERNMENT, None),  # Koulutoimisto (education offices)
        ("koulu", Categories.SCHOOL, None),  # Koulu (schools)
        (
            "lupapalvelu|erityislupa|lupa-asi",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Lupapalvelu (permit services, also at stations)
        ("poliisi", Categories.POLICE, None),  # Poliisi (police)
        ("tarkastus", Categories.OFFICE_GOVERNMENT, None),  # Tarkastus (inspection desks)
        ("kriisi|tukikeskus", Categories.SOCIAL_FACILITY, None),  # Kriisi (crisis services)
        ("päivystys", Categories.CLINIC_URGENT, None),  # Päivystys (emergency departments)
        ("sairaalamuseo", Categories.MUSEUM, None),  # Sairaalamuseo (hospital museums, cf. koulumuseo)
        ("päiväsairaala|kliininen", Categories.CLINIC, None),  # Päiväsairaala (day hospitals)
        ("potilasasia", Categories.OFFICE_GOVERNMENT, None),  # Potilasasia (patient-ombudsman desks)
        ("vainaja", None, None),  # Vainaja (morgues: no enum, stay generic)
        ("sairaala", Categories.HOSPITAL, None),  # Sairaala (hospitals)
        ("lähitori", Categories.SOCIAL_FACILITY, None),  # Lähitori (senior service points)
        ("konttori|kehitysyhtiö|yritystalo|kiinteistö oy", Categories.OFFICE_COMPANY, None),  # Konttori (head offices)
        ("kuraattori", Categories.SCHOOL, None),  # Kuraattori (school counsellors)
        ("luonnonsuojelualue", Categories.LEISURE_NATURE_RESERVE, None),  # Luonnonsuojelualue (nature reserves)
        ("arboretum", None, {"leisure": "botanical_garden"}),  # Arboretum (arboreta)
        ("erikoismetsä", None, {"natural": "wood"}),  # Erikoismetsä (designated municipal forests)
        ("teatteri|teater", Categories.THEATRE, None),
        ("kirkko|rukoushuone|raamattuhuone|kappeli", Categories.PLACE_OF_WORSHIP, None),  # Kirkko (churches)
        (
            "seurakuntatalo|seurakuntakoti|seurakuntakeskus|" "seurakuntatila",
            Categories.COMMUNITY_CENTRE,
            None,
        ),  # Seurakuntatalo (parish halls)
        ("muistomerkki|memorial|minnesmärk", Categories.TOURISM_ARTWORK, None),  # Muistomerkki (memorials)
        ("galleria|taiteen perusopetus", Categories.ARTS_CENTRE, None),  # Galleria (art galleries)
        ("linnoitus|lammasaitaus", Categories.TOURISM_ATTRACTION, None),  # Linnoitus (fortresses)
        ("monumentti", Categories.TOURISM_ARTWORK, None),  # Monumentti (monuments)
        ("patsas", Categories.TOURISM_ARTWORK, {"artwork_type": "sculpture"}),  # Patsas (statues)
        ("graffiti|graffitti", Categories.TOURISM_ARTWORK, {"artwork_type": "graffiti"}),  # Graffiti (graffiti walls)
        ("taidekontti", Categories.TOURISM_ARTWORK, None),  # Taidekontti (art containers)
        ("avanto|talviuinti", Categories.LEISURE_SWIMMING_AREA, None),  # Avanto / avantouinti (ice-swimming holes)
        ("luistelu", Categories.LEISURE_ICE_RINK, None),  # Luistelu (skating)
        (
            "lastenkoti|ryhmäkoti|ryhmäkodit|" "yhteisöllinen asuminen",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Lastenkoti (children homes)
        ("palveluasumisyksikkö", Categories.NURSING_HOME, None),  # Palveluasumisyksiköt (service-housing units)
        (
            "asumisyksikkö",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Asumisyksikkö (housing units)
        (
            "toimintakeskus|monitoimitalo|kerhotalo|"
            "harrastetila|harrastuskeskus|kerhohuone|"
            "asukastila|4h-kerho|kylätalo|seurantalo|"
            "työväentalo|kotiseututalo",
            Categories.COMMUNITY_CENTRE,
            None,
        ),  # Toimintakeskus (activity centres)
        ("olka-piste", Categories.OFFICE_GOVERNMENT, None),  # OLKA-pisteet (hospital info desks)
        (
            "yhdistys|kumppanuustalo|järjestötalo|yhteisötalo|" "yhteisökeskus|kulttuuritalo",
            Categories.COMMUNITY_CENTRE,
            None,
        ),  # Yhdistys (association houses)
        ("lastenkulttuurikeskus", Categories.ARTS_CENTRE, None),  # Lastenkulttuurikeskus (children's culture centres)
        (
            "kulttuurikeskus|kulttuuritila|yhteisötila",
            Categories.COMMUNITY_CENTRE,
            None,
        ),  # Kulttuurikeskus (culture centres)
        ("kokoustila", Categories.EVENTS_VENUE, None),  # Kokoustila (meeting rooms)
        ("neuvottelu", Categories.SOCIAL_FACILITY, None),  # Neuvottelu (negotiation centres, all family-affairs)
        ("pelastusasema|vpk|palokunta|paloasema", Categories.FIRE_STATION, None),  # Pelastusasema (rescue stations)
        ("linja-autoasema|bussiasema", Categories.BUS_STATION, None),  # Linja-autoasema (bus stations)
        ("huoltoasema", None, None),  # Huoltoasema (fuel stations): no precise filing, keep generic
        ("rautatieasema", None, {"railway": "station", "public_transport": "station"}),
        ("ilmailukeskus", None, {"aeroway": "aerodrome"}),  # Ilmailukeskus (sport-aviation fields)
        (
            "kunnanvirasto|kaupungintalo|kaupunginvirasto|"
            "office|lautakunta|valtuusto|hankinta|hankinnat|"
            "tonttijako|maakuntatalo",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Kunnanvirasto (municipal offices)
        ("liikelaitos", Categories.OFFICE_COMPANY, None),  # Liikelaitos (municipal business enterprises)
        (
            "keskusrekisteri|kunnantalo|hallinto|virasto",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Keskusrekisteri (parish register offices)
        (
            "päihde|arviointiyksikkö|tutkimusyksik|" "akuuttiosasto|vuodeosasto|kuntoutusyksikkö",
            Categories.CLINIC,
            None,
        ),  # Päihde (substance-abuse care)
        ("oy:n toimisto", Categories.OFFICE_COMPANY, None),  # Oy:n toimisto (company offices)
        ("toimisto", Categories.OFFICE_GOVERNMENT, None),  # Toimisto (offices)
        ("luontotupa", Categories.COMMUNITY_CENTRE, None),  # Luontotupa (nature huts keep the hut over info desks)
        (
            "matkailuneuvon|matkailuinfo",
            Categories.TOURISM_INFORMATION,
            {"information": "office"},
        ),  # Matkailuneuvonta (tourist info)
        ("toimipiste|palvelupaikka|toimipaikka", Categories.OFFICE_GOVERNMENT, None),  # Toimipiste (service points)
        ("museo", Categories.MUSEUM, None),  # Museo (museums)
        ("asiakaspalvelu", Categories.OFFICE_GOVERNMENT, None),  # Asiakaspalvelu (customer service)
        ("klubitalo", Categories.COMMUNITY_CENTRE, None),  # Klubitalo (peer clubhouses, not clinics)
        ("perhekeskus", Categories.OFFICE_GOVERNMENT, None),  # Perhekeskus (family centres)
        ("perhetyö", Categories.SOCIAL_FACILITY, None),  # Perhetyö (family work)
        (
            "kirjaamo|raatihuone|perheoikeudelliset|" "vapaa-aikatoimi",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Kirjaamo (registries)
        ("vapaa-aikakeskus", Categories.COMMUNITY_CENTRE, None),  # Vapaa-aikakeskus (leisure centres)
        (
            "kulttuuri- ja vapaa-aika|maistraatti|sivistys|"
            "maaseutu|varhaiskasvatus|perusopetus|työllisyys|"
            "työvoima|rakennusvalvonta|ympäristönsuojelu|"
            "rakennusvalvonnan|maanmittauslaitos|metsäkeskus|"
            "ulosotto|ympäristökeskus|kaupunkikehitys|"
            "ympäristövalvonta|terveysvalvonta|ympäristöterveys|elintarviketurvallisuus|pysäköinninvalvonta",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Kunnan kulttuuri- ja vapaa-aika (municipal culture/leisure depts)
        ("kotihoito", Categories.SOCIAL_FACILITY, None),  # Kotihoito (home care, outranks lähipalvelualue below)
        ("tulli", Categories.OFFICE_GOVERNMENT, None),  # Tulli (customs offices)
        ("kuntoutusohjaus", Categories.SOCIAL_FACILITY, None),  # Kuntoutusohjaus (rehab guidance)
        (
            "ohjaus|neuvonta|lähipalvelu|ohjaamo|" "asiointipiste|hyvinvointikioski",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Ohjaus (guidance desks)
        ("kioski", Categories.SHOP_KIOSK, None),  # Kioski (kiosks)
        (
            "palvelupiste|serviceenhet|palvelutori|" "navigaattori",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Palvelupiste (service points)
        ("palvelukeskus", Categories.SOCIAL_FACILITY, None),  # Palvelukeskus (service centres)
        ("palvelutalo", Categories.NURSING_HOME, None),  # Palvelutalo (sheltered housing)
        ("seniori", Categories.SOCIAL_FACILITY, None),  # Seniori (senior centres, outranks info desks below)
        ("luustoinfo|kansalaisinfo", Categories.OFFICE_GOVERNMENT, None),  # Luustoinfo (bone-health info desks)
        ("info", Categories.TOURISM_INFORMATION, {"information": "office"}),  # Info (city information desks)
        ("visitor centre|visitor center", Categories.TOURISM_INFORMATION, {"information": "visitor_centre"}),
        ("sosiaali", Categories.SOCIAL_FACILITY, None),  # Sosiaali (social services)
        ("vanhainkoti|hoivakoti", Categories.NURSING_HOME, None),  # Vanhainkoti (elderly homes)
        ("hoiva", Categories.SOCIAL_FACILITY, None),  # Hoiva (care homes)
        (
            "työpaja|kulttuuripaja|innopaja|taitopaja",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "workshop"},
        ),  # Työpaja (workshops)
        ("ikäihmisten päivätoiminta", Categories.SOCIAL_FACILITY, None),  # Day activities for elderly
        ("kehitysvamma|vammais", Categories.SOCIAL_FACILITY, None),  # Kehitysvamma (developmental-disability services)
        (
            "lyhytaikaishoito|lyhytaikaishoidon|" "lyhytaikaisyksikkö",
            Categories.NURSING_HOME,
            None,
        ),  # Lyhytaikaishoito (respite care)
        ("palvelut", Categories.OFFICE_GOVERNMENT, None),  # Palvelut (municipal service units)
        (
            "palvelukoti|palveluasumi|palveluasunnot|" "palvelukodit",
            Categories.NURSING_HOME,
            None,
        ),  # Palvelukoti (service homes)
        ("palvelu", Categories.OFFICE_GOVERNMENT, None),  # Palvelu (service desks)
        ("turvakoti", Categories.SOCIAL_FACILITY, {"social_facility": "shelter"}),
        ("päivätoiminta|päiväaikainen", Categories.SOCIAL_FACILITY, None),  # Päivätoiminta (day activities)
        ("al-anon|vertaistuki", Categories.COMMUNITY_CENTRE, None),  # Al-Anon (peer support)
        ("lastensuojelu", Categories.SOCIAL_FACILITY, None),  # Lastensuojelu (child welfare)
        ("vertaisryhm|sydänkerho", Categories.COMMUNITY_CENTRE, None),  # Vertaisryhmä (peer-support groups)
        ("sydänosasto|sydänyksikkö", Categories.CLINIC, None),  # Sydänosasto (cardiac wards)
        ("asumi|boende|bostad|bostäder|hemmet|kuntout", Categories.SOCIAL_FACILITY, None),  # Asumi (housing services)
        ("työterveys", Categories.CLINIC, None),  # Työterveys (occupational health)
        ("matonpesu", Categories.CARPET_WASHING, None),  # Matonpesu / matonpesupaikka (carpet washing)
        ("kierrätys|kiertopiste|hyötykäyttö|hyödyksi", Categories.RECYCLING, None),  # Kierrätys (recycling)
        ("hävikkiterminaali", Categories.SOCIAL_FACILITY, None),  # Hävikkiterminaali (surplus-food terminals)
        ("terminaali", Categories.FERRY_TERMINAL, None),  # Terminaali (ferry passenger terminals)
        (
            "vaateapu|tavara-apu|ruoka-apu|ruokajako|hävikki",
            Categories.SOCIAL_FACILITY,
            None,
        ),  # Vaateapu (clothing aid)
        ("hautausmaa", None, {"landuse": "cemetery"}),  # Hautausmaa (cemeteries, incl. pet cemeteries)
        ("krematorio", None, {"amenity": "crematorium"}),  # Krematorio (crematoriums)
        ("kodat", Categories.SHELTER, None),  # Kodat (kota shelters, plural)
        ("varikko", None, {"amenity": "depot"}),  # Varikko (depots)
        (
            "lajitteluasema|lajittelupiha|siirtokuormausasema",
            Categories.RECYCLING,
            None,
        ),  # Lajitteluasema (sorting stations)
        ("kaatopaikka", None, {"landuse": "landfill"}),  # Kaatopaikka (dump sites, incl. snow dumps)
        ("lähiasema|selviämis|sydänasema", Categories.CLINIC, None),  # Lähiasemat (local health stations)
        ("ensihoito", Categories.FIRE_STATION, None),  # Ensihoitoasemat (EMS stations)
        ("ekoasema", Categories.RECYCLING, None),  # Ekoasemat (eco recycling points)
        ("kohtaamisasema|miesten asema", Categories.COMMUNITY_CENTRE, None),  # Kohtaamisasemat (meeting points)
        ("businessasema", Categories.OFFICE_GOVERNMENT, None),  # BusinessAsema (business service point)
        ("puolustusasema", Categories.TOURISM_ATTRACTION, None),  # Puolustusasemat (war-history sites)
        ("kaavoitus", Categories.OFFICE_GOVERNMENT, None),  # Kaavoitus (planning offices)
        ("testausasema|testiasema", None, None),  # Testausasemat (test stations): no precise filing, keep generic
        ("asema", None, {"railway": "station", "public_transport": "station"}),  # Asema (railway stations)
        ("vuokraamo", Categories.SHOP_RENTAL, None),  # Vuokraamo (rental shops)
        ("kirpputori|kirppis|reshop", Categories.SHOP_SECOND_HAND, None),  # Kirpputori (flea markets)
        ("viljelypalsta|marjapensas|siirtolapuutarha", Categories.ALLOTMENTS, None),  # Viljelypalsta (allotments)
        ("lainaamo", Categories.TOOL_LIBRARY, None),  # Lainaamo (lending libraries)
        ("ulkoilualue", Categories.LEISURE_PARK, None),  # Ulkoilualue (outdoor areas)
        ("leirikeskus|leirialue|leiriytymispaikka", Categories.TOURISM_CAMP_SITE, None),  # Leirikeskus (camp centres)
        ("ampumarata", None, {"leisure": "shooting_ground", "sport": "shooting"}),  # Ampumarata (shooting ranges)
        ("leirintäalue|telttailu", Categories.TOURISM_CAMP_SITE, None),  # Leirintäalue (camping grounds)
        ("virkistysalue", Categories.LEISURE_PARK, None),  # Virkistysalue (recreation areas)
        ("laavu", Categories.SHELTER, None),  # Laavu (lean-to shelters)
        (
            "kalastusalue",
            None,
            {"leisure": "fishing"},
        ),  # Kalastusalue (fishing areas; after laavu so area shelters keep shelter)
        ("hätämajoitus|ensikoti", Categories.SHELTER, None),  # Hätämajoitus (emergency housing)
        ("luontokeskus", Categories.MUSEUM, None),  # Luontokeskus (nature centres)
        ("vessa", Categories.TOILETS, None),  # Vessa (toilets)
        ("talvipuutarha|kasvitieteelli", None, {"leisure": "botanical_garden"}),  # Talvipuutarha (botanical garden)
        ("asukaspuiston kerho", None, None),  # Asukaspuiston kerho (park club activities, not the park)
        ("kiintorasti", None, None),  # Kiintorasti (fixed orienteering controls, not the host park)
        ("urheilupuisto", Categories.LEISURE_SPORTS_CENTRE, None),  # Urheilupuisto (sports parks, cf. liikuntapuisto)
        ("puisto|puistikko", Categories.LEISURE_PARK, None),  # Puisto (parks)
        ("veistos", None, {"tourism": "artwork", "artwork_type": "sculpture"}),  # Veistos (sculptures; parks keep park)
        ("taideteos", Categories.TOURISM_ARTWORK, None),  # Taideteos (artworks)
        ("päiväkeskus", Categories.SOCIAL_FACILITY, None),  # Päiväkeskus (day centres)
        ("autiotupa", Categories.TOURISM_WILDERNESS_HUT, None),  # Autiotupa (wilderness huts)
        ("tupa", Categories.COMMUNITY_CENTRE, None),  # Tupa (meeting houses, compound-final)
        ("talkoolaituri", Categories.TOOL_LIBRARY, None),  # Talkoolaituri (tool-lending clean-up sheds, not piers)
        ("laituri", Categories.MAN_MADE_PIER, None),  # Laituri (piers)
        ("venepaikka", Categories.MARINA, None),  # Venepaikka (boat berths)
        ("vesipiste|vedenjakelu|vesiposti", Categories.DRINKING_WATER, None),  # Vesipiste (drinking-water points)
        ("veneenlaskupaikka", Categories.LEISURE_SLIPWAY, None),  # Veneenlaskupaikka (boat launch ramps)
        (
            "lintutorni",
            Categories.TOURISM_VIEWPOINT,
            {"man_made": "tower", "tower:type": "observation"},
        ),  # Lintutorni (bird towers)
        ("lintulava", Categories.TOURISM_VIEWPOINT, None),  # Lintulava (birdwatching platforms)
        (
            "luontotorni|näköalatorni",
            Categories.TOURISM_VIEWPOINT,
            {"man_made": "tower", "tower:type": "observation"},
        ),  # Luontotorni (nature towers)
        (
            "sairaanhoito|korvaushoito|vieroitus|leikkaus|"
            "anestesia|sisätauti|silmätauti|syöpätauti|"
            "sairaansija|tehohoito|munuais|tähystys|dialyysi|"
            "neulanvaihto|tartuntatauti",
            Categories.CLINIC,
            None,
        ),  # Sairaanhoito (nursing care)
        ("hoitokoti|hoitokodit", Categories.NURSING_HOME, None),  # Hoitokoti (care homes)
        ("eläinhoitola|lintuhoitola", Categories.VETERINARY, None),  # Eläinhoitola (animal-care clinics)
        ("hoito", Categories.OFFICE_GOVERNMENT, None),  # Hoito (care service desks)
        (
            "väestönsuoja|yhteiskalliosuoja",
            Categories.MILITARY_BUNKER,
            {"bunker_type": "bomb_shelter"},
        ),  # Väestönsuoja (civil-defence shelters)
        ("korsu", Categories.MILITARY_BUNKER, None),  # Korsu (war-history dugouts, e.g. Salpa Line)
    )

    # tori matches standalone and market compounds (kauppatori) but never
    # auditorio/laboratorio/toimisto, which do not end in tori.
    @staticmethod
    def _bare_or_compound(body: str) -> "re.Pattern[str]":
        # Standalone or compound-final stems: one shape for both site lists.
        return re.compile(r"(?:\b(?:" + body + r")\b|\w+(?:" + body + r")\b)")

    TORI_RE = _bare_or_compound("tori")
    SAUNA_RE = _bare_or_compound(r"saunat?")

    # Single capitalized token ("Sampola", "Muurola"): municipality,
    # locality and unit tails share one shape.
    SINGLE_CAP_RE = re.compile(r"[A-ZÅÄÖ][a-zåäö-]+")
    DIGIT_RE = re.compile(r"\d")

    @staticmethod
    def _is_single_cap(text: str) -> bool:
        return PtvFISpider.SINGLE_CAP_RE.fullmatch((text or "").strip()) is not None

    @staticmethod
    def _has_digit(text: str | None) -> bool:
        return PtvFISpider.DIGIT_RE.search(text or "") is not None

    @staticmethod
    def _has_no_digit(text: str | None) -> bool:
        return PtvFISpider.DIGIT_RE.search(text or "") is None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ids: list[str] = []
        self._seen_pages: set[int] = set()
        self._page_skips = 0
        # Detail batches emit once: a dead list page falls through to the
        # errback below, which continues with the ids collected so far.
        self._batches_emitted = False
        # Bounded-window org join: channel items wait only for their own
        # org batch (one round-trip), never the whole crawl.
        self._org_names: dict[str, str | None] = {}
        self._org_types: dict[str, str] = {}
        self._seen_orgs: set[str] = set()
        self._pending: dict[str, list[Feature]] = {}
        venue_words = (
            {w for keys, _, _ in self.CATEGORY_RULES for w in keys.split("|")}
            | set(self.BRANCH_TAILS)
            | set(self.UNIT_TAILS)
            | set(self.SERVICE_HEADS)
            | set(self.ROOM_WORDS)
            | {
                "toimisto",
                "asema",
                "talo",
                "keskus",
                "piste",
                "tupa",
                "maja",
                "sauna",
                "ranta",
                "tori",
                "kota",
                "laavu",
                "huone",
                "kerros",
                "alue",
                "järjestämispaikka",
                "opetuspiste",
                "toimipaikka",
                "uimarannat",
            }
        ) - {"telttailu"}
        # "telttailu" stays out of the fixture vocabulary: as a table key it
        # would otherwise flip island tent pairs ("Gåsgrund / Telttailupaikka")
        # into backwards head+located splits via the venue-evidence
        # fallthrough. The camp_site category is unaffected (table reads the
        # signed form).
        self.GENERIC_WORDS = {w.lower() for w in venue_words}
        self.FIXTURE_RE = re.compile("|".join(re.escape(w) for w in sorted(self.GENERIC_WORDS, key=len, reverse=True)))
        self._rules = []
        for keys, cat, extra in self.CATEGORY_RULES:
            # One alternation per same-target group: the table loop only
            # uses .search() truthiness, and every member shares the target,
            # so a single regex is exactly equivalent to per-key patterns.
            self._rules.append((re.compile("|".join(self._key_part(k) for k in keys.split("|"))), cat, extra))

    @staticmethod
    def _key_part(k: str) -> str:
        # Alternation branch for one table key: special keys keep their
        # guards (compound-end, lookarounds, boundaries), plain keys match
        # as escaped substrings. Shapes mirror the old per-key regexes.
        if k in ("lab", "kirkko", "kappeli", "seurakuntatalo", "halli", "tupa"):
            # Compound-end only: Tykslab/Fimlab, Aurejärven kirkko and
            # Säkylähalli match; labyrintti, Kirkkojärvi, Kirkkopuisto,
            # hallitus and maaseutupalvelut (tupa mid-compound) do not.
            return r"\w*" + re.escape(k) + r"\b"
        if k == "info":
            # Info desks read prefix or suffix (Infopiste, Pääinfo);
            # Sinfonia never matches.
            return r"info\b|\binfo"
        if k == "tulli":
            # Customs offices (Lentotulli) share the stem with
            # district/building names (Tullinkulma et al): those never match.
            return r"tulli(?!nkulma|kamari|vuor|saar|npuomi|ntori|aukio|naukio)"
        if k == "melonta":
            # Canoeing routes (melontareitti, melontareitit) are routes,
            # not venues: tracks and trails stay generic like retkeilyreitti.
            return r"melonta(?!reit)"
        if k == "käräjä":
            # Courthouse streets (Käräjätuvankuja) hosting allotment parcels
            # are allotments, not courts: viljelypalsta tails win.
            return r"käräjä(?!.*(?:viljelypalsta|marjapensas|siirtolapuutarha))"
        if k == "kioski":
            # Info kiosks are info points, not shops ("Infokioski",
            # "kioski eli infopiste"): the info rule below files them.
            return r"(?<!info)(?<!info-)kioski(?!\s*eli\s*infopiste)"
        if k == "skola":
            # Askola the municipality is not a skola (school); Eskola
            # farm compounds ("Eskolakoti") are not schools either, while
            # Swedish school compounds and inflections still file.
            return r"(?<!a)skol(a|an|ans|as|or|orna|ornas|anin)?\b"
        if k == "koulu":
            # Koulutalo, koulukoti and koulun stay schools; koulutus
            # and its inflections (koulutukseen/tukset) plus pupils
            # (koululainen) and school-aged (kouluikäinen, kouluiässä)
            # never match. Street words (koulutie, -katu, -kuja,
            # -polku, -väylä) never file as schools either.
            return r"\w*koulu(?!tus|tuk|lai|ikä|iä|tie|katu|kuja|polku|väylä)"
        if k == "asema":
            # Station words, compound-final only: lending the airport
            # ("...lentoasemalla") never files as a station; desks there
            # file as offices via their own later rules. A bare
            # Lentoasema is no one's railway station, and inflected
            # station modifiers ("metroaseman väestönsuoja",
            # "terveysasemilla" services) must not file as stations.
            # Rautatieasema keeps its own earlier rule.
            return r"(?<!lento)asema\b"
        if k in ("nuoriso", "nuorten"):
            # Youth councils (Nuorisovaltuusto) are civic offices, not venues.
            return re.escape(k) + r"(?!valtuusto)"
        if k == "puistikko":
            # Park streets ("Onnikoti Puistikkotie", a care home on
            # Puistikko road) are addresses, not parks: only the
            # diminutive itself files as a park (Lentäjänpuistikko).
            return r"puistikko(?!tie)"
        return re.escape(k)

    def _count(self, key: str, n: int = 1) -> None:
        crawler = getattr(self, "crawler", None)
        stats = crawler.stats if crawler else None
        if stats is None:
            return
        stats.inc_value(f"{self.name}/{key}", n)

    def list_url(self, page: int) -> str:
        return f"{self.api_base_url}{self.LIST_PATH}?" + urlencode({"page": page})

    async def start(self):
        yield JsonRequest(url=self.list_url(1), cb_kwargs={"page": 1}, errback=self.errback_list)

    def errback_list(self, failure) -> Iterable[JsonRequest]:
        # A dead list page must not stall the crawl: the retry middleware
        # already had its chance, so skip ahead one page (bounded: past-end
        # pages answer successfully and stop the chain in parse, while
        # repeated deaths fall through to the ids collected so far).
        request = getattr(failure, "request", None)
        url = getattr(request, "url", "") or ""
        self._count("page/failed")
        page = (getattr(request, "cb_kwargs", None) or {}).get("page", 0)
        yield from self._skip_or_emit(page, url)

    def _skip_or_emit(self, page: int, url: str) -> Iterable[JsonRequest]:
        # A dead list page must not stall the crawl: skip ahead (bounded),
        # else fall through to the ids collected so far. Shared by failed
        # pages and 200-but-garbage bodies, which the retry middleware
        # never retries.
        if isinstance(page, int) and page >= 1 and page + 1 not in self._seen_pages and self._page_skips < 3:
            self._page_skips += 1
            self._count("page/skipped")
            self.logger.error("list page %d failed, skipping ahead: %s", page, url)
            self._seen_pages.add(page + 1)
            yield JsonRequest(url=self.list_url(page + 1), cb_kwargs={"page": page + 1}, errback=self.errback_list)
            return
        self.logger.error("list page failed, continuing with %d ids: %s", len(self._ids), url)
        yield from self._emit_batches()

    def parse(self, response: TextResponse, page: int) -> Iterable[JsonRequest]:
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("page/bad_json")
            self.logger.error("bad JSON from %s", response.url)
            yield from self._skip_or_emit(page, response.url)
            return
        if not isinstance(payload, dict):
            self._count("page/bad_shape")
            yield from self._skip_or_emit(page, response.url)
            return
        self._seen_pages.add(page)
        self._page_skips = 0
        before_ids = set(self._ids)
        known_ids = set(self._ids)
        for row in payload.get("itemList") or []:
            if isinstance(row, dict) and row.get("id") and str(row["id"]) not in known_ids:
                known_ids.add(str(row["id"]))
                self._ids.append(str(row["id"]))
                self._count("list/ids")
        total = payload.get("pageCount")
        if isinstance(total, int) and page < total and page + 1 not in self._seen_pages:
            yield JsonRequest(url=self.list_url(page + 1), cb_kwargs={"page": page + 1}, errback=self.errback_list)
            return
        if not isinstance(total, int) and payload.get("itemList"):
            # Server ignoring ?page would loop forever on page 1's shape.
            if page + 1 not in self._seen_pages and set(self._ids) > before_ids:
                yield JsonRequest(url=self.list_url(page + 1), cb_kwargs={"page": page + 1}, errback=self.errback_list)
                return
        yield from self._emit_batches()

    def _emit_batches(self) -> Iterable[JsonRequest]:
        # Detail batches emit exactly once, from the final list page or from
        # the list errback when a page dies mid-chain.
        if self._batches_emitted:
            return
        self._batches_emitted = True
        yield from self._batch_requests()

    def errback_batch(self, failure) -> Iterable[Feature]:
        # Detail batches carry no pending items (channels parse on success),
        # so a dead batch only needs counting and logging, never flushing.
        request = getattr(failure, "request", None)
        url = getattr(request, "url", "") or ""
        self._count("batch/failed")
        self.logger.error("detail batch failed: %s", url)
        yield from ()

    def _batch_requests(self) -> Iterable[JsonRequest]:
        # Detail endpoint takes comma-joined guids (repeated ?guids= params
        # return only the first); batch_size keeps URLs short (see above).
        for i in range(0, len(self._ids), self.batch_size):
            chunk = self._ids[i : i + self.batch_size]
            yield JsonRequest(
                url=f"{self.api_base_url}{self.DETAIL_PATH}?" + urlencode({"guids": ",".join(chunk)}),
                callback=self.parse_batch,
                errback=self.errback_batch,
            )

    # Operator QIDs verified against Wikidata (exact fi names only;
    # anything else yields the name without a QID, never a guess).
    REGISTER_KEEPERS = frozenset({"Suomen Apteekkariliitto"})

    OPERATORS_WIKIDATA = {
        "Helsingin kaupunki": "Q1757",
        "Espoon kaupunki": "Q47034",
        "Vantaan kaupunki": "Q127623",
        "Kauniaisten kaupunki": "Q208287",
        "Länsi-Uudenmaan hyvinvointialue": "Q110245203",
        "Vantaan ja Keravan hyvinvointialue": "Q110245340",
        "Itä-Uudenmaan hyvinvointialue": "Q110245220",
        "Kela": "Q3557354",
        "Suomen valtio": "Q33",
    }

    # Private daycare chains as brand-heads ("Pilke Kilonkallio"):
    # the chain operates the unit even when the city purchased it.
    CHAIN_OPERATORS = (("pilke", "Pilke"), ("norlandia", "Norlandia"))

    @staticmethod
    def _org_head(org_name: str) -> str:
        # Department suffixes strip to the legal entity ("Helsingin kaupunki,
        # Kasvatuksen ja koulutuksen toimiala" is the city); bare names
        return org_name.split(",", 1)[0].strip() or org_name

    @staticmethod
    def _org_supersedes(named_operator: str, org_name: str) -> bool:
        # The org record denotes the same entity more fully: its tokens strictly
        # contain the named operator's, so the record wins; unrelated maintainers
        # never qualify.
        head_tokens = set(re.findall(r"\w+", (named_operator or "").lower()))
        org_tokens = set(re.findall(r"\w+", (org_name.split(",", 1)[0].strip() or org_name).lower()))
        return len(head_tokens) >= 2 and head_tokens < org_tokens

    def _apply_operator_tags(
        self, item: Feature, operator: str, full_org_name: str | None = None, org_type: str | None = None
    ) -> None:
        # Wikidata QID, operator:type (private vs. religious) and
        # association-office demotion: shared by both operator passes.
        if qid := self.OPERATORS_WIKIDATA.get(operator):
            item["operator_wikidata"] = qid
        else:
            self._count("operator/no_qid")
        is_company = self._is_company_name(operator)
        private_org = (
            self._is_private_org(operator)
            or (bool(full_org_name) and self._is_private_org(full_org_name.split(",", 1)[0].strip()))
            or (
                org_type == "Company"
                and "liikelaitos" not in operator.lower()
                and "liikelaitos" not in (full_org_name or "").lower()
            )
        )
        if is_company or private_org:
            # Companies and associations delivering public services are
            # private operators, following the Oy/Ab precedent.
            # Privacy reads the full name so stripped acronyms ("RIKU")
            # don't launder associations public.
            item["extras"]["operator:type"] = "private"
        elif re.search(r"(seurakunta|församling)", operator, flags=re.IGNORECASE) or re.search(
            r"\bsrk\b", operator, flags=re.IGNORECASE
        ):
            # Parishes are public-law religious bodies: operator:type marks
            # the religious organizer without claiming anything about the
            # service itself (seurakuntatalo clubs et al).
            self._count("operator/religious")
            item["extras"]["operator:type"] = "religious"
        if private_org and not is_company and org_type != "Company" and self._tag(item, "office") == "government":
            # Association-run desks are association offices, not government
            # ones (office lives in extras; a top-level write would raise).
            # Record-proven and marker-proven companies keep the government
            # office filing (Oy parity); only the operator type turns private.
            self._count("operator/office_demoted")
            item["extras"]["office"] = "association"

    def _apply_operator(self, item: Feature, org_name: str | None, org_type: str | None = None) -> None:
        if item.get("operator"):
            if org_name and self._org_supersedes(item["operator"], org_name):
                # The joined record names the same operator more fully;
                # clear the provisional tags and let the record replace the
                # signed short form.
                self._count("operator/org_superseded")
                item.pop("operator_wikidata", None)
                (item.get("extras") or {}).pop("operator:type", None)
                # A provisional association demotion never survives a public
                # record supersede (the pair would claim a public operator
                # running an association office).
                (item.get("extras") or {}).pop("office", None)
            else:
                # Branch-agency suffixes ("/Kela") already named the provider,
                # as did slash tails: the joined record never replaces them,
                # and its context never retypes them (the record describes
                # the maintainer, which may be a company while the named
                # provider is a national agency). Only the QID enriches.
                if qid := self.OPERATORS_WIKIDATA.get(item["operator"]):
                    item["operator_wikidata"] = qid
                else:
                    self._count("operator/no_qid")
                self._count("operator/branch_agency")
                return
        if (
            org_name
            and re.search(r"(hyvinvointialue|sairaanhoitopiiri)", org_name, flags=re.IGNORECASE)
            and self._tag(item, "amenity") == "school"
            and re.fullmatch(
                r".*(?:^|\s)(lukio|koulu|yhteiskoulu|peruskoulu)\s*", (item.get("name") or "").strip().lower()
            )
        ):
            # Wellbeing-area channels named bare schools are the student-health
            # units there, not the schools (municipalities run schools):
            # file the clinic, keep the building name.
            self._count("category/school_health_unit")
            apply_category(Categories.CLINIC, item)
        for stem, brand in self.CHAIN_OPERATORS:
            if re.match(stem + r"\b", (item.get("name") or "").lower()):
                self._count("operator/chain_brand")
                item["operator"] = brand
                item["extras"]["operator:type"] = "private"
                return
            if (
                re.search(r"\b" + stem + r"\b", (item.get("name") or "").lower())
                and self._tag(item, "amenity") == "kindergarten"
            ):
                # Chain-operated units with a service-worded head ("Päiväkoti
                # Pilke Äppelbo"): the brand still operates them.
                self._count("operator/chain_brand_mid")
                item["operator"] = brand
                item["extras"]["operator:type"] = "private"
                return
        if not org_name:
            self._count("operator/unattributed")
            return
        if org_name.split(",", 1)[0].strip() in self.REGISTER_KEEPERS or org_name in self.REGISTER_KEEPERS:
            self._count("operator/register_keeper")
            return
        # Department and brand suffixes name the desk/brand, not the operator;
        # association tails stay, short marker-less tails strip.
        operator = self._org_head(org_name)
        if "/" in operator:
            head_org, _, tail_org = operator.rpartition("/")
            if (
                head_org.strip()
                and tail_org.strip()
                and self._has_operator_word(head_org)
                and not self._has_operator_word(tail_org)
            ):
                # Project/unit tails on association names ("Pohjois-Savon
                # Muisti ry / Pohjois-Savon Muistiluotsi"): the legal entity
                # operates, the project does not.
                self._count("operator/slash_project_split")
                operator = head_org.strip()
        if (dash := re.search(r"\s+[–—-]\s+(\S.*)$", operator)) is not None:
            tail = dash.group(1).strip()
            if re.search(r"\b(och|för|av|på|till|med|förbund|förening)\b", tail, flags=re.IGNORECASE) or (
                len(tail.split()) <= 3
                and not re.search(
                    r"(oy|ab|ry|r\.y\.?|tmi|toiminimi|ky|säätiö|yhdistys|förening|seurakunta)",
                    tail,
                    flags=re.IGNORECASE,
                )
            ):
                operator = operator[: dash.start()].strip() or operator
                self._count("operator/brand_stripped")
        item["operator"] = operator
        self._apply_operator_tags(item, operator, org_name, org_type)

    def parse_batch(self, response: TextResponse) -> Iterable[Feature]:
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("batch/bad_json")
            return
        if not isinstance(payload, list):
            self._count("batch/bad_shape")
            return
        fresh_orgs: list[str] = []
        for channel in payload:
            if not isinstance(channel, dict):
                self._count("batch/skipped_row")
                continue
            try:
                item = self.parse_channel(channel)
            except Exception:  # noqa: BLE001 - one malformed record never kills the batch
                self._count("batch/record_error")
                self.logger.error("ptv_fi: dropping malformed record %s", channel.get("id"))
                continue
            if item:
                raw_org_id = channel.get("organizationId")
                org_id = str(raw_org_id) if raw_org_id else ""
                if not org_id:
                    self._apply_operator(item, None)
                    yield item
                elif org_id in self._org_names:
                    self._apply_operator(item, self._org_names[org_id], self._org_types.get(org_id))
                    yield item
                else:
                    self._pending.setdefault(org_id, []).append(item)
                    if org_id not in self._seen_orgs:
                        self._seen_orgs.add(org_id)
                        fresh_orgs.append(org_id)
        for i in range(0, len(fresh_orgs), self.batch_size):
            chunk = fresh_orgs[i : i + self.batch_size]
            yield JsonRequest(
                url=f"{self.api_base_url}{self.ORG_PATH}?" + urlencode({"guids": ",".join(chunk)}),
                callback=self.parse_orgs,
                errback=self.errback_orgs,
                # Retries after a failure must not die in the dupefilter:
                # a re-request with the same URL would silently drop its
                # callback/errback and strand the waiting items.
                dont_filter=True,
                # Snapshot the chunk: response URLs cannot be trusted to
                # still carry guids= (redirects may strip the query).
                cb_kwargs={"org_ids": chunk},
            )

    def parse_orgs(self, response: TextResponse, org_ids=None) -> Iterable[JsonRequest | Feature]:
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("org/bad_json")
            yield from self._flush_request_orgs(self._request_org_ids(response))
            return
        if not isinstance(payload, list):
            self._count("org/bad_shape")
            yield from self._flush_request_orgs(self._request_org_ids(response))
            return
        for org in payload:
            if not isinstance(org, dict) or not org.get("id"):
                self._count("org/skipped_row")
                continue
            org_id = str(org["id"])
            name = self._lang_value(org.get("organizationNames") or [], "fi", "sv", "en")
            org_type = org.get("organizationType") or ""
            self._org_names[org_id] = name
            self._org_types[org_id] = org_type
            for item in self._pending.pop(org_id, []):
                self._apply_operator(item, name, org_type)
                yield item
        # Orgs requested but unreturned (deleted/renamed rows) are known
        # operator-less from here on: later items join at once instead of
        # re-requesting, because a re-request with the same URL would die
        # in the dupefilter and strand its items until close. Flush the
        # leftovers like the failure paths.
        requested = list(org_ids) if org_ids is not None else self._request_org_ids(response)
        for org_id in requested:
            self._org_names.setdefault(org_id, None)
        yield from self._flush_request_orgs(requested)

    def _request_org_ids(self, response_or_failure) -> list[str]:
        # Requested org ids, snapshotted from the request first: response
        # URLs cannot be trusted to carry guids= (redirects may strip the
        # query, and a missing param would strand items exactly like the
        # fixed dupefilter bug). Falls back to the URL for harness doubles.
        request = getattr(response_or_failure, "request", None)
        cb_ids = (getattr(request, "cb_kwargs", None) or {}).get("org_ids")
        if cb_ids:
            return list(cb_ids)
        url = getattr(request, "url", "") or ""
        if not url:
            url = getattr(response_or_failure, "url", "") or ""
        match = re.search(r"guids=([^&]*)", url)
        return unquote(match.group(1)).split(",") if match else []

    def _flush_request_orgs(self, org_ids: Iterable[str]) -> Iterable[Feature]:
        # Flush the window without operators rather than losing it.
        # Flushed ids leave _seen_orgs so a later batch re-requests them
        # on the failure paths instead of stranding new items in a
        # never-joined window; ids already known-missing join at once via
        # _org_names without re-requesting.
        for org_id in org_ids:
            self._seen_orgs.discard(org_id)
            for item in self._pending.pop(org_id, []):
                self._apply_operator(item, None)
                yield item

    def errback_orgs(self, failure) -> Iterable[Feature]:
        self._count("org/failed")
        yield from self._flush_request_orgs(self._request_org_ids(failure))

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        from scrapy import signals

        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider, reason=None) -> None:
        leftover = {org_id: len(items) for org_id, items in self._pending.items() if items}
        if leftover:
            self._count("org/unflushed_on_close", sum(leftover.values()))
            # Operator-imposed early stops always truncate the queue:
            # expected truncation, not data loss. Anything else means
            # org joins genuinely never arrived.
            truncated = reason in ("closespider_timeout", "closespider_itemcount")
            log = self.logger.warning if truncated else self.logger.error
            log("ptv_fi: unflushed org windows on close: %d orgs (reason=%s)", len(leftover), reason)

    # Contact-details placeholders filed as names ("Kontaktuppgifter"
    # with no Finnish name): never POI names, fall back to real ones.
    NAME_PLACEHOLDERS = frozenset({"kontaktuppgifter"})

    def _names(self, channel: dict) -> dict[str, str]:
        # The official Name wins over AlternativeName ("Talaskankaan
        # retkeilyreitti", not "Talaskangas"); displayNameType breaks
        # ties, first-listed wins otherwise. Single-name records behave
        by_lang: dict[str, list[tuple[str, str]]] = {}
        for row in channel.get("serviceChannelNames") or []:
            if not isinstance(row, dict):
                continue
            lang = row.get("language")
            value = self._visible((row.get("value") or "").strip())
            if lang and value and value.casefold() not in self.NAME_PLACEHOLDERS:
                by_lang.setdefault(lang, []).append((row.get("type") or "", value))
        display = [
            (row.get("type"), row.get("language"))
            for row in (channel.get("displayNameType") or [])
            if isinstance(row, dict)
        ]
        out: dict[str, str] = {}
        fi_slashes: int | None = None
        for lang, variants in sorted(by_lang.items(), key=lambda kv: kv[0] != "fi"):
            picked = None
            for dtype, dlang in display:
                if dlang == lang:
                    picked = next((v for t, v in variants if t == dtype), None)
                    break
            if picked is None:
                picked = next((v for t, v in variants if t == "Name"), None)
                if picked is None and lang != "fi" and fi_slashes is not None:
                    # No display guidance and no Name type: follow the
                    # Finnish structure so slash twins stay parallel
                    # ("Integrationsservice / Vasa stad ..." for a slash
                    # pair, not the bare "Integrationstjänster").
                    picked = next((v for _, v in variants if v.count(" / ") == fi_slashes), variants[0][1])
                elif picked is None:
                    picked = variants[0][1]
            out[lang] = picked
            if lang == "fi":
                fi_slashes = picked.count(" / ")
        return out

    def _is_dropped_name(self, name_fi: str) -> str | None:
        lowered = name_fi.lower()
        if "suojatie" in lowered:
            # Audio-guided crosswalks are road furniture, not POIs.
            return "non_place/crosswalk"
        if lowered.endswith("keittiö") and any(w in lowered for w in self.KITCHEN_INFIX):
            # Institutional kitchens inside daycares/schools/hospitals.
            return "non_place/kitchen"
        if "kirjastoauto" in lowered:
            # Bookmobiles are routes, not fixed POIs.
            return "non_place/bookmobile"
        if re.search(r"\btesti", lowered):
            # Published test/template rows ("Kuvan testipiste").
            return "non_place/test_data"
        if "sähköpostiosoite" in lowered:
            # Contact channels published as locations ("Sipoon Veden
            # sähköpostiosoite"): an email address is not a visit point.
            return "non_place/contact"
        if self.MOBILE_RE.search(lowered):
            # Outreach/mobile services with a depot address, no visitable premises.
            return "non_place/mobile"
        if (
            self.TRACK_RE.search(lowered)
            or any(word in lowered for word in self.TRACK_WORDS)
            or self.KM_RE.search(lowered)
        ):
            # Tracks, loop trails and distance-marked routes are linear, not places.
            if self._track_names_venue(lowered):
                return None
            return "non_place/track"
        return None

    def _track_names_venue(self, lowered: str) -> bool:
        # Venue heads inside track-word names (running straights of named
        # halls, outdoor gyms, courts at track-named parks) mark visitable
        # premises; bare compounds ("Nevanlenkki", "Pakopirtin latu",
        # school-owned tracks) never qualify.
        if "ulkokuntoilu" in lowered:
            return True
        if re.search(r"juoksu(suora|rata)", lowered) and self.TRACK_VENUE_RE.search(lowered):
            return True
        return bool(self.TRACK_PLACE_RE.search(lowered) and self.TRACK_FACILITY_RE.search(lowered))

    def _visit_address(self, channel: dict) -> dict | None:
        # Location addresses are visit points; Postal ones are mailing only.
        best = None
        for address in channel.get("addresses") or []:
            if not isinstance(address, dict) or address.get("type") != "Location":
                continue
            street = address.get("streetAddress") or {}
            if not isinstance(street, dict):
                continue
            if best is None or (address.get("subType") == "Single" and best.get("subType") != "Single"):
                best = address
        return best

    @classmethod
    def _lang_value(cls, rows: list, *langs: str) -> str | None:
        by_lang = {}
        for row in rows or []:
            if isinstance(row, dict) and row.get("language") not in by_lang:
                value = cls._visible((row.get("value") or "").strip())
                if value:
                    by_lang[row.get("language")] = value
        for lang in langs:
            if by_lang.get(lang):
                return by_lang[lang]
        for value in by_lang.values():
            if value:
                return value
        return None

    # WGS84 bounds for Finland: degree-pairs misfiled as TM35FIN never overlap these ranges.
    WGS84_BOUNDS = (59.0, 71.0, 19.0, 32.0)

    def _coords(self, street: dict) -> tuple[float, float] | None:
        # Fields are named latitude/longitude but hold TM35FIN
        # northing/easting; convert to WGS84 lon/lat. NotReceived/Failed
        # states mark placeholder coords.
        if (street.get("coordinateState") or "") in ("NotReceived", "Failed"):
            self._count("coords/dropped_state")
            return None
        try:
            northing = float(str(street.get("latitude")))
            easting = float(str(street.get("longitude")))
        except (TypeError, ValueError, AttributeError):
            return None
        lat_lo, lat_hi, lon_lo, lon_hi = self.WGS84_BOUNDS
        if lat_lo <= northing <= lat_hi and lon_lo <= easting <= lon_hi:
            # Degrees filed as TM35FIN ("Sarkkirannan laavu" with
            # latitude 64.916102, longitude 25.47273): already WGS84,
            # never transform (TM35FIN eastings/northings never overlap
            # these ranges).
            self._count("coords/wgs84_degrees")
            return easting, northing
        try:
            lon, lat = self._transformer.transform(easting, northing)
        except ValueError:
            return None
        if not (
            self.WGS84_BOUNDS[0] <= lat <= self.WGS84_BOUNDS[1] and self.WGS84_BOUNDS[2] <= lon <= self.WGS84_BOUNDS[3]
        ):
            return None
        state = street.get("coordinateState") or "missing"
        self._count(
            {"Ok": "coords/ok", "EnteredByUser": "coords/entered"}.get(
                state, "coords/missing" if state == "missing" else "coords/other"
            )
        )
        return lon, lat

    # Tails naming institutions are venues; the facility names the POI.
    # Narrower than the service-map list on purpose.
    INSTITUTION_TAILS = tuple(
        "koulu lukio yläaste ala-aste sairaala kirjasto museo teatteri kirkko kappeli päiväkoti opisto "
        "uimahalli terveysasema neuvola virasto hammashoitola poliklinikka skolan ".split()
    )
    # Precompiled end-anchored institution check shared by _is_institution
    # (built from INSTITUTION_TAILS so the two can never drift apart).
    INSTITUTION_RE = re.compile(r"\w*(?:" + "|".join(INSTITUTION_TAILS) + r")$")
    # Branch-office designators name the org's local desk, not a venue
    # ("Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka"): keep the head.
    BRANCH_TAILS = tuple("toimipiste toimipaikka toimisto ".split())
    # Hosted school units: the unit is the POI, the school the venue
    # ("Kellon koulu, Kiviniemen yksikkö").
    UNIT_TAILS = tuple("yksikkö opetuspiste ryhmäkoti ".split())
    # Service areas and category-descriptors are designations, never venues.
    AREA_TAILS = tuple("lähipalvelualue palvelualue toiminta-alue ulkoilusaari ".split())

    def _island_area(self, text: str) -> bool:
        # Island service areas are places, not designations
        # ("Kahvila / Ulkoilusaari"): they locate the POI. The area
        # word itself must be island-flavoured: Vuosaari districts
        # containing "saari" still drop.
        return "ulkoilusaari" in text.lower()

    def _is_bare_area(self, text: str) -> bool:
        # Bare administrative areas ("Tikkurilan alue") are coverage,
        # never venues. Real outdoor venues (ulkoilualue, virkistysalue,
        # luonnonsuojelualue) are multiword and never match.
        lowered = text.lower()
        return re.search(r"(^|\s)alue$", lowered) is not None

    def _is_unit_tail(self, text: str) -> bool:
        # Bare unit qualifiers ("Himangan yksikkö") without a host venue
        # name one service with their head: keep whole (cf. Stadin).
        return any(word in text.lower() for word in (*self.UNIT_TAILS, "toimipiste", "toimipaikka"))

    def _is_venue_head(self, head: str) -> bool:
        # Venue heads host splits (their units name the POI there);
        # service heads merge with their qualifiers instead. Fixture
        # alone is not enough: service words ("terapia") are fixtures too.
        lowered = head.lower()
        return self._is_institution(lowered) or (
            self._has_fixture(head) and not any(word in lowered for word in self.SERVICE_TAILS)
        )

    def _is_street_head(self, head: str) -> bool:
        # Pure street/address heads are never venues ("Kurkisuontie 2",
        # "Kenttäpolku"): the address line carries them. Shores stay out
        # (ranta doubles as a venue suffix).
        suffixes = tuple(s for s in self.STREET_SUFFIXES if s != "ranta")
        tokens = [t.strip(",.;") for t in head.split() if t.strip(",.;")]
        if not tokens:
            return False
        if any(re.fullmatch(self.HOUSENUMBER_RE.pattern, t) for t in tokens):
            return any(t.lower().endswith(suffixes) for t in tokens if not re.fullmatch(self.HOUSENUMBER_RE.pattern, t))
        return len(tokens) == 1 and tokens[0].lower().endswith(suffixes)

    # Physical rooms/fields: venue-named unless numbered or proper-named.
    ROOM_WORDS = tuple(
        "sali kenttä halli allas rata tila huone koppi katos kota laavu grillipaikka heittopaikka "
        "huoltorakennus ulkokuntoilupaikka pumptrack ".split()
    )
    # Single memorial objects never split (title + designation of one artwork).
    MEMORIAL_WORDS = tuple("muistomerkki monumentti patsas memorial ".split())
    # Service heads hosted at schools: the service names the POI, the
    # school is the venue ("Opiskeluhuolto, Karhusuon koulu", cf. the
    # service-map comma-venue rule). Slash pairs already resolve this way.
    SERVICE_HEADS = tuple("opiskeluhuolto kouluterveydenhuolto opiskeluterveydenhuolto ".split())
    # Generic service words heading "<service>, <unit>" names
    # ("Kuvantaminen, Pirkkala Pirkkalan röntgen"; "Fysiatrian
    # poliklinikka, Vaasa", the county's Vaasa branch) and branch-carrying
    # institutions ("Vantaan musiikkiopisto"): the head names the POI,
    # the remainder the branch.
    BRANCH_HEADS = tuple("kuvantaminen laboratorio näytteenotto poliklinikka musiikkiopisto ".split())
    # Service/unit nouns for host<>facility inversion, both directions
    # ("Lasten puheterapia, Perhekeskus Pohjatuuli" and its mirror).
    SERVICE_TAILS = tuple(
        "yksikkö ryhmäkoti lastenkoti opetuspiste neuvola terapia poliklinikka hammashoitola kuntoutus "
        "rokotus vastaanotto ravintola keittiö kahvila kioski kauppa apteekki neuvonta ohjaus palvelu opastus "
        "päivätoiminta kalastuspaikka opiskeluhuolto kouluterveydenhuolto opiskeluterveydenhuolto ".split()
    )
    # Hospital acronyms operate the unit; they name no venue (", Tyks";
    # "OYSin ..."). Prefixes and comma tails strip off the applied name.
    HOSPITAL_ACRONYMS = frozenset("TYKS OYS HUS TAYS KYS ".split())
    # Bare acronym units at hospital heads ("Vatsakeskus, Tays Hatanpää")
    # are hospital departments: unit words licensing the clinic filing.
    ACRONYM_UNIT_WORDS = tuple("keskus yksikkö osasto klinikka poliklinikka vastaanotto ".split())
    # Swedish institution words for bilingual dash names (cf. Eskola: the
    # boundary keeps Finnish Eskola/places whole).
    SWEDISH_WORD_RE = re.compile(
        r"\b(apotek(et)?|skola(n)?|daghem(met)?|bibliotek(et)?|simhall(en)?|idrottshall(en)?|servicehem(met)?)",
        re.IGNORECASE,
    )
    # Branch-of-agency suffixes name the service provider, never the POI
    # ("Kokemäen Asiointipiste/Kela" is the city's desk serving Kela).
    AGENCY_SUFFIX_RE = re.compile(r"/\s*kela\b(?=,|\s*$)", re.IGNORECASE)
    # Station-village post offices file under their municipality
    # ("ORIVESI AS" -> "Orivesi").
    STATION_SUFFIX_RE = re.compile(r"\s+as$", re.IGNORECASE)
    # Tails naming a school building (venue evidence, not filing): deliberately
    # wider/narrower than the neighboring sets (Swedish forms in, kirjasto/museo
    # out); unifying them would change filing.
    SCHOOL_TAIL_RE = re.compile(
        r"(koulu|lukio|opisto|päiväkoti|esiopetus|yläaste|ala-aste|skola|daghem|högstadium|lågstadium)"
    )
    # Shared school-host stems for _split_comma_school_host: deliberately the
    # narrow 4-stem set (other institution tails never locate group activities).
    SCHOOL_HOST_RE = re.compile(r"(koulu|lukio|opisto|päiväkoti)")
    SCHOOL_HOST_TAIL_RE = re.compile(r"(koulu|lukio|opisto|päiväkoti)$")

    def _is_institution(self, text: str) -> bool:
        return self.INSTITUTION_RE.search(text) is not None

    # Bureau/metadata tails stripped in order before splitting (each
    # result stripped; first match does not stop the chain). The post tails
    # are last because a stripped suffix can only be followed by arrangement text.
    CLEAN_SUBS_PRE = (
        (re.compile(r",\s*$"), ""),
        (re.compile(r"\s+,"), ","),
        (re.compile(r"\s*(\d+)\*\s*$"), r" \1"),
        (COORD_TAIL_RE, ""),
        (re.compile(r",\s*Kasvatuksen ja koulutuksen.*$"), ""),
        (re.compile(r",\s*Sektorn för fostran och utbildning.*$"), ""),
        (re.compile(r",\s*Education Division.*$"), ""),
        (AGENCY_SUFFIX_RE, ""),
    )
    CLEAN_SUBS_POST = (
        (re.compile(r"\s*-palvelun järjestämispaikka\s*(?:,\s*\d+)?\s*$"), ""),
        (re.compile(r",\s*palvelupaikka\s*$"), ""),
        (re.compile(r"\s+yhteystiedot(\s*,\s*[A-ZÅÄÖ][^,]*?)?\s*$"), ""),
        (re.compile(r"^päiväkoti[\s-]+(?=.*päiväkoti)", re.IGNORECASE), ""),
    )

    def _clean_name(self, raw: str) -> str:
        # Bureau tails are record metadata, not name parts (cf. service-map
        # unit 79871: bureau tails stripped the same way). A dangling
        # trailing comma (data-entry cut-off) strips first so boilerplate
        # patterns match ("... järjestämispaikka,").
        primary = raw.replace("\u00a0", " ").strip()
        for rx, repl in self.CLEAN_SUBS_PRE:
            primary = rx.sub(repl, primary).strip()
        before_boilerplate = primary
        for rx, repl in self.CLEAN_SUBS_POST:
            primary = rx.sub(repl, primary).strip()
        # A stripped suffix leaves the service's own name as-is ("Näe hyvä
        # mussa -leirit lapsille"): the remainder names the service, so
        # lowercase-dash descriptors never strip below.
        boilerplate_stripped = primary != before_boilerplate
        # Guide/contact qualifiers ("Nummelan kimppakävelyt Marin kanssa"):
        # a capitalized genitive-singular proper noun plus kanssa names the
        # person, never the venue (contact-person doctrine). Plural markers
        # (-jen/-den/-ien/-tten/-sten) and lowercase common nouns
        # ("Marttojen kanssa", "muistisairauden kanssa") are integral event
        # text and stay.
        kanssa_stripped = re.sub(r"\b[A-ZÅÄÖ][a-zåäö]+n(?<!jen|den|ien)(?<!tten|sten) kanssa,\s*", "", primary)
        kanssa_stripped = re.sub(r"\s*\b[A-ZÅÄÖ][a-zåäö]+n(?<!jen|den|ien)(?<!tten|sten) kanssa\b", "", kanssa_stripped)
        if kanssa_stripped != primary:
            self._count("name/person_dropped")
            primary = re.sub(r"\s{2,}", " ", re.sub(r"\s+,", ",", kanssa_stripped)).strip()
        primary = re.sub(r"^\S+\s+(?:ry:n|r\.y\.:n)\s+", "", primary).strip()
        if (yhdistys := re.match(r"^(\S+)\s+yhdistyksen\s+(.+)$", primary)) and not self._has_fixture(
            yhdistys.group(1)
        ):
            # Operator-headed associations ("Porvoon Yhdistyksen talo"):
            # venue-headed genitives ("Kuntosali yhdistyksen jäsenille",
            # audience, not operator) stay whole. Category evidence counts
            # too: bare proper-noun heads have neither.
            if self._category(yhdistys.group(1))[0] is None:
                primary = yhdistys.group(2).strip()
        dash = re.search(r"\s+-\s*([a-zåäö].*)$", primary)
        if (
            dash
            and not boilerplate_stripped
            and not re.search(
                r"(toimisto|kerho|ryhmä|klubi|piste|koulu|talo|keskus|asema|neuvonta|ohjaus|apteekki|kahvila"
                r"|toiminta|akatemia|opisto|kirjasto|museo|teatteri|kirkko|kappeli|lukio|klinikka|sairaala"
                r"|sali|kenttä|halli|allas|rata|tila|huone|koppi|katos|kota|laavu|väylä|latu|polku|baana|reitti|liikelaitos)",
                dash.group(1),
                flags=re.IGNORECASE,
            )
        ):
            # Lowercase dash descriptors ("Walonkulman Klubitalo -
            # yhteisö työikäisille"); unit tails split later instead.
            # A stranded conjunction keeps the whole ("salit ja -alueet").
            stripped = primary[: dash.start()].strip()
            if not re.search(r"(ja|tai|sekä|&|/|-)\s*$", stripped):
                primary = stripped
        return primary or raw.strip()

    def _branch_agency(self, raw: str) -> str | None:
        if self.AGENCY_SUFFIX_RE.search(raw):
            return "Kela"
        if re.search(r"\bkela(n)?\b", raw, flags=re.IGNORECASE):
            # Kela desks maintained by others ("Kelan asiointipiste
            # Lapinlahdella", city-run): the provider still names it.
            # Word-boundaried so Kelankatu and Siimakela never match.
            return "Kela"
        return None

    def _apply_branch(self, item: Feature, signed: str, shown: str, official: str | None, city_src: str | None) -> None:
        if agency := self._branch_agency(signed):
            # Branches of national agencies carry their provider
            # ("Kokemäen Asiointipiste/Kela"); kept over the maintainer.
            # Tags apply at the org join below, which sees the record.
            item["operator"] = agency
        if self._tag(item, "amenity") in ("school", "college", "kindergarten"):
            # branch=* is chain retail, not schools: campus qualifiers
            # stay in the name, never split off (cf. Stadin ammattiopisto).
            return
        comma_head = signed.split(",")[0].strip() if "," in signed else ""
        comma_low = comma_head.lower()
        if (
            "," in signed
            and (
                self._endswith_any(shown.lower(), self.BRANCH_HEADS)
                or any(comma_low == word or comma_low.startswith(word + " ") for word in self.BRANCH_HEADS)
            )
            and not comma_head.endswith("-")
        ):
            # Imaging/lab units read "<service>, <place> <unit>"
            # ("Kuvantaminen, Pirkkala Pirkkalan röntgen"): the service
            # names the POI, the remainder the branch. A dash-fragment
            # comma ("Korva-, nenä- ja ...") never separates.
            tail = signed.rpartition(",")[2].strip()
            first, _, rest = tail.partition(" ")
            if rest.strip() and city_src and first.casefold() == city_src.strip().casefold():
                tail = rest.strip()
            if tail and not (city_src and tail.casefold() == city_src.strip().casefold()):
                # A branch that merely repeats the city is not a branch.
                self._count("name/comma_branch_unit")
                item["branch"] = tail
        if not item.get("branch") and ":" in signed and "://" not in signed:
            head, _, tail = signed.rpartition(":")
            head, tail = head.strip(), tail.strip()
            if (
                head
                and self._is_single_cap(tail)
                and re.search(r"(toimisto|piste|yksikkö|asema|keskus)$", head.lower())
            ):
                # Colon branches ("...opiston toimisto: Sampola").
                self._count("name/colon_branch")
                item["branch"] = tail
        if not item.get("branch"):
            m = re.match(
                r"^(.*(?:toimipiste|toimipaikka|palvelupiste|asiointipiste)[^,]*),\s*([A-ZÅÄÖ][a-zåäö-]+)$",
                signed,
            )
            if m and (not city_src or m.group(2).casefold() != city_src.strip().casefold()):
                # Branch offices with city tails ("Liikunnan palvelupiste, Pöytyä").
                self._count("name/comma_branch_office")
                item["branch"] = m.group(2)
        branch = item.get("branch")
        if branch:
            located = item.get("located_in") or ""
            if located and (branch.casefold() in located.casefold() or located.casefold() in branch.casefold()):
                # A branch duplicating the venue is not a branch.
                self._count("name/branch_dup_located")
                del item["branch"]
            elif (shown or "").casefold() == branch.casefold():
                self._count("name/branch_dup_name")
                del item["branch"]
            elif city_src and branch.casefold() == city_src.strip().casefold():
                # A branch repeating the municipality ("Ivalo") is not a
                # branch; the city field carries it.
                self._count("name/branch_dup_city")
                del item["branch"]

    # Company/association markers for operator detection. Dotted forms
    # consume the trailing dot (Derby stays whole via the leading boundary).
    # Shared alternation (sr stays END_RE-only: a bare "Sr" tail is a name suffix).
    OPERATOR_MARKERS = r"oy|ab|ry|r\.y\.?|r\.f\.?|tmi|toiminimi|ky|ay|öb|ö\.b?\.?|säätiö"
    OPERATOR_END_RE = r"(\b(" + OPERATOR_MARKERS + r"|sr)|(yhdistys|förening|seurakunta))\.?$"
    PRIVATE_SUBSTRINGS = ("punainen risti", "setlementti", "attendo", "säätiö", "sininauha")
    # Municipalities (fi names, casefolded) derived from the CC0 raw dump
    # itself. Coverage-list tails match against these exactly, so fixture-bearing
    # towns peel as towns instead of filing as venues. Gaps err safe:
    # unknown towns keep the old heuristic path.
    MUNICIPALITIES = frozenset(
        "akaa alajärvi alavieska alavus asikkala askola aura brändö eckerö enonkoski enontekiö espoo eura "
        "eurajoki evijärvi finström forssa föglö geta haapajärvi haapavesi hailuoto halsua hamina hammarland "
        "hankasalmi hanko harjavalta hartola hattula hausjärvi heinola heinävesi helsinki hirvensalmi hollola "
        "huittinen humppila hyrynsalmi hyvinkää hämeenkyrö hämeenlinna ii iisalmi iitti ikaalinen ilmajoki "
        "ilomantsi imatra inari inkoo isojoki isokyrö janakkala joensuu jokioinen jomala joroinen joutsa "
        "juuka juupajoki juva jyväskylä jämijärvi jämsä järvenpää kaarina kaavi kajaani kalajoki kangasala "
        "kangasniemi kankaanpää kannonkoski kannus karijoki karkkila karstula karvia kaskinen kauhajoki "
        "kauhava kauniainen kaustinen keitele kemi kemijärvi keminmaa kemiönsaari kempele kerava keuruu "
        "kihniö kinnula kirkkonummi kitee kittilä kiuruvesi kivijärvi kokemäki kokkola kolari konnevesi "
        "kontiolahti korsnäs kotka kouvola kristiinankaupunki kruunupyy kuhmo kuhmoinen kumlinge kuopio "
        "kuortane kurikka kustavi kuusamo kyyjärvi kärkölä kärsämäki kökar lahti laihia laitila lapinjärvi "
        "lapinlahti lappajärvi lappeenranta lapua laukaa lemi lemland lempäälä leppävirta lestijärvi lieksa "
        "lieto liminka liperi lohja loimaa loppi loviisa luhanka lumijoki lumparland luoto luumäki maalahti "
        "maarianhamina marttila masku merijärvi merikarvia miehikkälä mikkeli muhos multia muonio mustasaari "
        "muurame mynämäki myrskylä mäntsälä mänttä-vilppula mäntyharju naantali nakkila nivala nokia "
        "nousiainen nurmes nurmijärvi närpiö orimattila oripää orivesi oulainen oulu outokumpu padasjoki "
        "paimio paltamo parainen parikkala parkano pedersören pelkosenniemi pello perho pertunmaa petäjävesi "
        "pieksämäki pielavesi pietarsaari pihtipudas pirkkala polvijärvi pomarkku pori pornainen porvoo posio "
        "pudasjärvi pukkila punkalaidun puolanka puumala pyhtää pyhäjoki pyhäjärvi pyhäntä pyhäranta pälkäne "
        "pöytyä raahe raasepori raisio rantasalmi ranua rauma rautalampi rautavaara rautjärvi reisjärvi "
        "riihimäki ristijärvi rovaniemi ruokolahti ruovesi rusko rääkkylä saarijärvi salla salo saltvik "
        "sastamala sauvo savitaipale savonlinna savukoski seinäjoki sievi siikainen siikajoki siikalatva "
        "siilinjärvi simo sipoo siuntio sodankylä soini somero sonkajärvi sotkamo sottunga sulkava sund "
        "suomussalmi suonenjoki sysmä säkylä taipalsaari taivalkoski taivassalo tammela tampere tervo tervola "
        "teuva tohmajärvi toholampi toivakka tornio turku tuusniemi tuusula tyrnävä ulvila urjala utajärvi "
        "utsjoki uurainen uusikaarlepyy uusikaupunki vaala vaasa valkeakoski vantaa varkaus vehmaa vesanto "
        "vesilahti veteli vieremä vihti viitasaari vimpeli virolahti virrat vårdö vöyri ylitornio ylivieska "
        "ylöjärvi ypäjä ähtäri äänekoski ".split() + ["koski tl", "maarianhamina - mariehamn", "pedersören kunta"]
    )

    def _post_city(self, office: str | None) -> str | None:
        if not (office or "").strip():
            return None
        return self.STATION_SUFFIX_RE.sub("", office.strip())

    def _municipality_name(self, street: dict, channel: dict) -> str | None:
        # Visit-point municipality first; channel service areas only when
        # they agree on a single municipality, else fall back to the post
        # office.
        mun = (street.get("municipality") or {}) if isinstance(street, dict) else {}
        if isinstance(mun, dict):
            if name := self._lang_value(mun.get("name") or [], "fi", "sv", "en"):
                return name.strip() or None
        seen: list[str] = []
        for area in channel.get("areas") or []:
            if not isinstance(area, dict):
                continue
            for row in area.get("municipalities") or []:
                if not isinstance(row, dict):
                    continue
                name = self._lang_value(row.get("name") or [], "fi", "sv", "en")
                stripped = (name or "").strip()
                if stripped and stripped not in seen:
                    seen.append(stripped)
        if len(seen) == 1:
            return seen[0]
        return None

    def _city_src(self, street: dict, channel: dict, office: str | None) -> str | None:
        if mun := self._municipality_name(street, channel):
            self._count("address/city_municipality")
            return mun
        self._count("address/city_postoffice")
        return self._post_city(office)

    def _is_memorial(self, *texts: str) -> bool:
        return any(word in text.lower() for text in texts for word in self.MEMORIAL_WORDS)

    @staticmethod
    def _strip_trailing_paren(text: str, fallback: bool = False) -> str:
        # Trailing parenthesised qualifiers ("... Oy (Helsinki)") read past
        # for detection; with fallback an all-paren tail yields the original.
        stripped = re.sub(r"\s*\([^()]*\)$", "", text.strip()).strip()
        return stripped or (text.strip() if fallback else stripped)

    def _has_operator_word(self, text: str) -> bool:
        # Short forms need word boundaries; longer forms match inside compounds.
        # A leading Tmi marks toiminimi operators. Trailing parenthesised
        # qualifiers read past for detection.
        stripped = self._strip_trailing_paren(text, fallback=True)
        return (
            re.search(r"^tmi\b", stripped, flags=re.IGNORECASE) is not None
            or re.search(self.OPERATOR_END_RE, stripped, flags=re.IGNORECASE) is not None
        )

    def _is_company_name(self, operator: str) -> bool:
        # Commercial legal forms (Oy, Ab, Tmi/toiminimi, Ky, Ay, Öb):
        # keep government office filings when running outsourced public
        # desks, never demote to association offices.
        stripped = self._strip_trailing_paren(operator, fallback=True)
        return (
            re.search(r"^tmi\b", stripped, flags=re.IGNORECASE) is not None
            or re.search(r"\b(oy|ab|tmi|toiminimi|ky|ay|öb|ö\.b?\.?)\.?$", stripped, flags=re.IGNORECASE) is not None
        )

    def _is_private_org(self, operator: str) -> bool:
        # Companies and associations delivering public services, marked or known
        # bare names. Parishes (seurakunta) are public-law bodies, never private,
        # unless carrying a company/association marker themselves.
        lowered = operator.lower()
        if "seurakunta" in lowered and not re.search(r"\b(oy|ab|ry|r\.y\.?|tmi|toiminimi)\b", lowered):
            return False
        # Trailing parenthesised qualifiers ("Yhdistys (NNKY)") shield the
        # marker from the end anchor: _has_operator_word reads past them for
        # detection only (the emitted operator keeps its full form).
        return (
            self._has_operator_word(operator)
            or re.search(r"\bry\b", operator, flags=re.IGNORECASE) is not None
            or re.search(r"\briku\b", operator, flags=re.IGNORECASE) is not None
            or re.search(r"\w*seura\b", lowered) is not None
            or re.search(r"\w*kerho\b", lowered) is not None
            or lowered.rstrip(".").endswith("kassa")
            or re.search(r"(jat|jät)$", lowered) is not None
            or any(sub in lowered for sub in self.PRIVATE_SUBSTRINGS)
        )

    @staticmethod
    def _tag(item: Feature, key: str) -> str | None:
        # Applied tags (amenity/office/...) land in extras (Feature rejects
        # them top-level); read the level that carries them.
        return (item.get("extras") or {}).get(key)

    def _is_operator_shaped(self, text: str) -> bool:
        # Company/association tails name the maintainer, never a venue
        # ("Imatran keilahalli Oy", "Ysti ry").
        return self._has_operator_word(text)

    def _has_fixture(self, text: str) -> bool:
        return self.FIXTURE_RE.search(text.lower()) is not None

    def _is_person(self, text: str) -> bool:
        # Two or three capitalized tokens with no venue evidence
        # ("Sari Wicklund"); named units with fixture nouns never match.
        return re.fullmatch(
            r"[A-ZÅÄÖ][a-zåäö-]+(?: [A-ZÅÄÖ][a-zåäö-]+){1,2}", text.strip()
        ) is not None and not self._has_fixture(text)

    # Tokenizer shared by person/venue checks ("Sipoon Enter", "Sari
    # Wicklund"): split on whitespace and punctuation alike.
    TOKEN_SPLIT_RE = re.compile(r"[\s,./():-]+")

    def _is_proper_tail(self, text: str) -> bool:
        # A non-initial capitalized tail token outside the generic
        # vocabulary names a distinctive unit.
        if self._is_operator_shaped(text):
            return False
        tokens = [t for t in self.TOKEN_SPLIT_RE.split(text) if t]
        return any(re.match(r"[A-ZÅÄÖ]", token) and token.lower() not in self.GENERIC_WORDS for token in tokens[1:])

    def _clean_located(self, located: str) -> str | None:
        # Operator tails, trailing cities and person names are not venues.
        if located.strip().casefold() in ("infopiste", "info"):
            # Bare info points are sub-facilities, never host venues.
            self._count("name/generic_venue_dropped")
            return None
        loc = re.sub(
            r"\s+\S*?(?:\b(?:" + self.OPERATOR_MARKERS + r")|(?:yhdistys|förening|seurakunta))\.?$",
            "",
            located.strip(),
            flags=re.IGNORECASE,
        ).strip(" ,")
        if loc != located.strip():
            self._count("name/operator_tail_stripped")
        paren = re.search(r"\s*\(([^()]*)\)$", loc)
        if paren and self.COMMA_STREET_RE.search(paren.group(1).lower()):
            # Parenthesised street addresses leaked into the venue
            # ("...peruskoulu (Solvindsgatan 11)"): the address line
            # carries them, never located_in.
            self._count("name/located_paren_address_dropped")
            loc = loc[: paren.start()].strip(" ,")
        if not loc:
            return None
        if re.search(r"(toiminta|toimintaa|toimintaan)$", loc.lower()) and not self._has_fixture(loc):
            # Bare activity descriptors are services, not venues
            # ("Allas - Tantsut / Ite ja yhessä - toiminta").
            self._count("name/activity_tail_dropped")
            return None
        if "," in loc:
            pre, _, city = loc.rpartition(",")
            if pre.strip() and self._has_fixture(pre) and not self._has_fixture(city) and self._is_single_cap(city):
                self._count("name/city_tail_stripped")
                loc = pre.strip()
        if self._is_person(loc):
            self._count("name/person_dropped")
            return None
        return loc

    def _located_or(self, text: str) -> str:
        # Cleaned venue, or the raw text when cleaning drops nothing
        # usable: the venue half of a pair always locates something.
        return self._clean_located(text) or text

    def _split_pair(self, shown: str, venue_text: str, official: str | None, strict: bool = False) -> SplitTriple:
        # One triple-return shape for located-venue pairs: fallback keeps the
        # raw venue text, strict yields None when unusable.
        return shown, self._clean_located(venue_text) if strict else self._located_or(venue_text), official

    def _is_room_tail(self, tail: str) -> bool:
        return any(word in tail.lower() for word in self.ROOM_WORDS)

    def _resolve_slash_room(self, head: str, tail: str, name: str, tag: str) -> SplitTriple | None:
        # Rooms/fields are the facility, the host the venue.
        # Self-named pairs stay whole instead.
        if not self._is_room_tail(tail):
            return None
        if head.lower().endswith(tail.lower()):
            self._count("name/slash_self_kept")
            return name, None, None
        self._count("name/slash_numbered_room" if self._has_digit(tail) else tag)
        return self._split_pair(tail, head, name)

    def _slash_inst_unit(self, head: str, tail: str, name: str) -> SplitTriple | None:
        if any(word in tail.lower() for word in (*self.UNIT_TAILS, "toimipiste", "toimipaikka")):
            # Administrative units hosted at institutions
            # ("Laihian Keskuskoulu / Yläkoulun yksikkö").
            self._count("name/slash_facility")
            return self._split_pair(tail, head, name, strict=True)
        return None

    def _slash_inst_room(self, head: str, tail: str, name: str) -> SplitTriple | None:
        return self._resolve_slash_room(head, tail, name, "name/slash_room")

    def _slash_inst_ground(self, head: str, tail: str, name: str) -> SplitTriple | None:
        if "lähiliikuntapaikka" in tail.lower():
            # Exercise grounds hosted at institutions: the ground names
            # the POI, the school the venue; Swedish heads resolve below.
            self._count("name/slash_exercise_ground")
            return self._split_pair(tail, head, name, strict=True)
        return None

    def _resolve_slash_institution(self, head: str, tail: str, name: str) -> SplitTriple | None:
        # Institution-headed pairs: hosted units, rooms and exercise
        # grounds name the POI, the institution the venue.
        if not (self._is_institution(head.lower()) and not self._is_institution(tail.lower())):
            return None
        return self._first_hit(
            (self._slash_inst_unit, self._slash_inst_room, self._slash_inst_ground), head, tail, name
        )

    def _slash_street_head(self, head: str, tail: str, name: str) -> SplitTriple | None:
        if self._is_street_head(head):
            # Streets and street addresses are never venues
            # ("Kurkisuontie 2 / Hiekkakenttä"): the facility names
            # the POI, the address line carries the street.
            self._count("name/slash_street_head")
            return tail, None, name
        return None

    def _slash_numbered_building(self, head: str, tail: str, name: str) -> SplitTriple | None:
        if re.search(r"(rakennus|talo)\s*\d", tail.lower()) or "huoltorakennus" in tail.lower():
            # Numbered buildings qualify the head facility ("Eläintarhan
            # urheilukenttä / Huoltorakennus 4"): neither venues nor POIs.
            # Bare utility buildings never pose as the POI either: the
            # venue head names it ("Väinämöisenkenttä / Huoltorakennus").
            self._count("name/slash_building_kept")
            return head, None, name
        return None

    def _slash_pair_structural(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        # Street heads, numbered buildings and hosted units resolve before
        # service/venue dispatch below. tail_base unused; kept for the
        return self._first_hit(
            (self._slash_street_head, self._slash_numbered_building, self._resolve_slash_institution),
            head,
            tail,
            name,
        )

    @staticmethod
    def _comma_base(text: str) -> str:
        # Comma descriptors strip to the head ("Kulosaaren ala-aste,
        # Liikkis" names the school, not the club).
        return text.split(",")[0].strip()

    @staticmethod
    def _endswith_any(lowered: str, words) -> bool:
        # str.endswith takes a tuple directly; this folds the repeated
        # any(x.endswith(w) for w in ...) shapes into one call site.
        if isinstance(words, str):
            words = (words,)
        return lowered.endswith(tuple(words))

    @staticmethod
    def _keep_official(sub: SplitTriple, name: str) -> SplitTriple:
        # Re-dispatch preserving the signed form as official: the sub-split
        # names/locates, the outer signed form survives in official_name.
        return sub[0], sub[1], name

    @staticmethod
    def _cap_first(text: str | None) -> str | None:
        # Capitalize-first with the empty guard folded in.
        return text[0].upper() + text[1:] if text else text

    def _resolve_slash_pair(self, head: str, tail: str, name: str) -> SplitTriple | None:
        # Institution, service, place and person tails resolve against the
        # head; returns None to fall through to room/appositive handling.
        tail_base = self._comma_base(tail)
        return self._first_hit(
            (self._slash_pair_structural, self._slash_pair_service_area, self._slash_pair_venue_person),
            head,
            tail,
            tail_base,
            name,
        )

    def _slash_exercise_ground(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if "lähiliikuntapaikka" in tail.lower() and re.search(r"(koulu|skol)\w*", head.lower()):
            # Exercise grounds at schools, Finnish or Swedish
            # ("Vuoniityn peruskoulu / ...", "Åshöjdens grundskola /
            # Lähiliikuntapaikka"): the ground names the POI, the
            # school the venue (cf. slash_room; skol covers
            # skola/skolan, which institution tails lack).
            self._count("name/slash_exercise_ground")
            return self._split_pair(tail, head, name, strict=True)
        return None

    def _slash_subunit_kept(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if tail_base.lower() in ("koulutus",):
            # Education-subunit descriptors ("Sivistysosasto / Koulutus"):
            # the department names it whole; the subunit is not a venue.
            self._count("name/slash_subunit_kept")
            return name, None, None
        return None

    def _slash_area_kept(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if self._is_bare_area(tail_base):
            # Bare coverage areas are not venues ("X / Tikkurilan alue"):
            # the signed form stays whole, never split into located_in.
            self._count("name/slash_area_kept")
            return name, None, None
        return None

    def _slash_unit_kept(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if self._is_unit_tail(tail_base) and not self._is_institution(head.lower()):
            # Unit qualifiers of a service without a host venue
            # name one service: keep whole.
            self._count("name/slash_unit_kept")
            return name, None, None
        return None

    def _slash_service_tail(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if any(word in tail_base.lower() for word in self.SERVICE_TAILS) and not self._is_institution(head.lower()):
            # Service-tailed pairs name the service ("Perhekeskus /
            # Neuvola", "Salmen ulkoilualue / Kalastuspaikka"); the venue
            # hosts it. Precedes the institution rule, except against
            # institution heads, which resolve first. Substring (not
            # end-anchored) so plural service desks ("ruokapalvelut")
            # resolve too.
            self._count("name/slash_service_unit")
            return self._split_pair(tail, head, name)
        return None

    def _slash_pair_service_area(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        # Exercise grounds, subunit descriptors, coverage areas, unit
        # qualifiers and service tails resolve before venue dispatch below.
        return self._first_hit(
            (
                self._slash_exercise_ground,
                self._slash_subunit_kept,
                self._slash_area_kept,
                self._slash_unit_kept,
                self._slash_service_tail,
            ),
            head,
            tail,
            tail_base,
            name,
        )

    def _slash_institution_venue(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if self._is_institution(tail_base.lower()):
            # Named institutions as tails are venues
            # ("Iltapäivätoiminta / Steiner-koulu"); comma descriptors
            # ride along ("... / Kulosaaren ala-aste, Liikkis").
            self._count("name/slash_institution_venue")
            return self._split_pair(head, tail_base, name)
        return None

    def _slash_place_facility(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if self._has_fixture(tail) and re.search(r"(stadion|areena|keskus|puisto)$", head.lower()):
            # Place-headed pairs name the facility, preceding the district
            # guess: stadiums end in -n without being districts.
            self._count("name/slash_place_facility")
            return self._split_pair(tail, head, name)
        return None

    def _slash_district_facility(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if re.fullmatch(r"[A-ZÅÄÖ][a-zåäöA-ZÅÄÖ-]+n", head) and " " not in head and self._has_fixture(tail):
            # Bare genitive-district head ("Pohjois-Espoon /
            # Niipperin matonpesupaikka"): the facility is the name.
            self._count("name/slash_district_facility")
            return tail, None, name
        return None

    def _slash_person_drop(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if self._is_person(tail):
            # Contact persons are not venues ("Sari Wicklund"); host-named
            # units share a token with their school ("Sipoon Enter").
            head_tokens = {t.lower() for t in self.TOKEN_SPLIT_RE.split(head) if len(t) >= 4}
            tail_tokens = {t.lower() for t in self.TOKEN_SPLIT_RE.split(tail) if len(t) >= 4}
            if not (head_tokens & tail_tokens):
                self._count("name/person_dropped")
                return head, None, name
        return None

    def _slash_office_kept(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if re.search(r"(toimisto|toimipiste|toimipaikka|virasto)$", head.lower()) and re.search(
            r"(toimipiste|toimipaikka)", tail.lower()
        ):
            # Office desks at office heads ("Keurusselän ...toimisto /
            # Mänttä-Vilppulan toimipiste"): the qualifier belongs in
            # the name (Stadin rule for offices).
            self._count("name/slash_office_kept")
            return name, None, None
        return None

    def _slash_service_proper(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if (
            any(word in head.lower() for word in self.SERVICE_TAILS)
            and not self._is_institution(head.lower())
            and self._is_proper_tail(tail)
        ):
            # Services at proper-named venues ("Iltapäivätoiminta /
            # Leikkipuisto Nurkka"): the service names the POI, the
            # venue hosts it.
            self._count("name/slash_service_proper")
            return self._split_pair(head, tail, name)
        return None

    def _slash_proper_facility(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        if self._is_proper_tail(tail):
            self._count("name/slash_proper_facility")
            return self._split_pair(tail, head, name, strict=True)
        return None

    def _slash_generic_room(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        return self._resolve_slash_room(head, tail, name, "name/slash_generic_room")

    def _slash_pair_venue_person(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        # Institution, place and person tails resolve against the head;
        # rooms close the dispatch.
        return self._first_hit(
            (
                self._slash_institution_venue,
                self._slash_place_facility,
                self._slash_district_facility,
                self._slash_person_drop,
                self._slash_office_kept,
                self._slash_service_proper,
                self._slash_proper_facility,
                self._slash_generic_room,
            ),
            head,
            tail,
            tail_base,
            name,
        )

    def _peel_slash_pair(self, segments: list[str]) -> tuple[str, str | None] | None:
        # Peel trailing descriptor segments from the right (bounded);
        # returns (head, tail) with tail None when all peeled.
        segs = list(segments)
        for _ in range(3):
            if len(segs) < 2:
                break
            tail = segs[-1]
            if not tail or len(tail) <= 1:
                return None
            lowered = tail.lower()
            if (
                self.COMMA_STREET_RE.search(lowered)
                or (
                    len(tail) >= 7
                    and " " not in tail.strip()
                    and re.search(r"(" + self.STREET_STEM_ALT + r")$", lowered)
                )
                or any(word in lowered for word in self.AREA_TAILS)
                or self._is_memorial(tail)
            ):
                self._count("name/slash_descriptor_dropped")
                segs.pop()
                continue
            break
        if len(segs) < 2:
            return (segs[0], None)
        return (" / ".join(segs[:-1]), segs[-1])

    def _strip_venue_org(self, tail: str) -> str:
        # Operator organisations inside the venue ("Steiner-koulu,
        # Helsingin Rudolf ...yhdistys", often feed-truncated): the
        # school part is the venue.
        if "," not in tail:
            return tail
        venue_head, _, venue_org = tail.partition(",")
        if venue_head.strip() and re.search(
            r"(\b(?:" + self.OPERATOR_MARKERS + r")\b|(?:yhdistys|förening|seurakunta))",
            venue_org,
            flags=re.IGNORECASE,
        ):
            self._count("name/slash_venue_org_stripped")
            return venue_head.strip()
        return tail

    def _slash_paren_address(self, segments: list[str], name: str) -> SplitTriple | None:
        tail = segments[-1]
        venue = self._strip_trailing_paren(tail)
        if venue != tail and venue and self.COMMA_STREET_RE.search(tail.lower()):
            # Parenthesised street address inside the last venue
            # ("Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)").
            self._count("name/slash_paren_address")
            return venue, None, name
        return None

    def _slash_area_island(self, segments: list[str], name: str) -> SplitTriple | None:
        if len(segments) >= 2 and self._island_area(segments[-1]):
            # Island service areas locate the POI ("Kahvila /
            # Ulkoilusaari") instead of peeling the island away.
            self._count("name/slash_area_island")
            return " / ".join(segments[:-1]), segments[-1], name
        return None

    def _slash_island_venue(self, segments: list[str], name: str) -> SplitTriple | None:
        if (
            len(segments) == 2
            and re.search(r"\w*(saari|luoto)$", segments[0].strip().lower())
            and self._has_fixture(segments[1])
        ):
            # Island-headed facility pairs ("Kaunissaari / Telttailu- ja
            # leiriytymispaikka 2."): the facility names the POI instead.
            self._count("name/slash_island_venue")
            return segments[1].strip(), segments[0].strip(), name
        return None

    def _slash_bay_venue(self, segments: list[str], name: str) -> SplitTriple | None:
        if (
            len(segments) == 2
            and re.search(r"\w+lahti$", segments[0].strip().lower())
            and self._has_fixture(segments[1])
        ):
            # Bay-headed facility pairs: the facility names the POI, the bay
            # locates it. Compound heads only, so the city of Lahti never matches.
            self._count("name/slash_bay_venue")
            return segments[1].strip(), segments[0].strip(), name
        return None

    def _slash_sculpture_kept(self, segments: list[str], name: str) -> SplitTriple | None:
        if (
            len(segments) == 2
            and " " not in segments[1]
            and "veistos" in segments[1].lower()
            and not self._is_operator_shaped(segments[1])
        ):
            # Single sculpture designations ("Moduli / Rakentajaveistos"):
            # title + designation of one artwork; peeling or splitting
            # would strand a fragment, so the signed form stays whole.
            self._count("name/slash_sculpture_kept")
            return name, None, None
        return None

    def _slash_geo_pair(self, segments: list[str], name: str) -> SplitTriple | None:
        # Geographic pre-checks run before descriptor peeling: addresses,
        # island areas/heads, bay heads and single sculptures.
        return self._first_hit(
            (
                self._slash_paren_address,
                self._slash_area_island,
                self._slash_island_venue,
                self._slash_bay_venue,
                self._slash_sculpture_kept,
            ),
            segments,
            name,
        )

    def _slash_operator_pair(self, head: str, tail: str, name: str, segments: list[str]) -> SplitTriple | None:
        # Operator heads/tails and memorials resolve between peeling and
        # pair dispatch. Tail arrives venue-org-stripped from _split_slash.
        if self._is_operator_shaped(head) and len(segments) == 2:
            # Operator-headed records ("Ysti ry / ..."): the head is the
            # maintainer, the tail a service description, not a venue.
            self._count("name/slash_operator_head")
            return head, None, name
        if self._is_operator_shaped(tail) and len(segments) == 2:
            # Operator-tailed records ("Imatra Bowling Center / Imatran
            # keilahalli Oy"): the head names the POI, the tail strips to
            # its venue part. Pure operator tails ("... / Eläinten hyväksi
            # EHY ry") are maintainers, never venues.
            self._count("name/slash_operator_tail")
            located = self._clean_located(tail)
            if located is not None and not self._has_fixture(located):
                located = None
            return head, located, name
        if self._is_memorial(head, tail):
            self._count("name/slash_memorial")
            return name, None, None
        return None

    def _split_slash(self, name: str) -> SplitTriple | None:
        # Spaced slash chains: peel descriptors, then resolve the pair.
        if " / " not in name:
            return None
        segments = [s.strip() for s in name.split(" / ")]
        if (geo := self._slash_geo_pair(segments, name)) is not None:
            return geo
        peeled = self._peel_slash_pair(segments)
        if peeled is None:
            return None
        head, tail = peeled
        if tail is None:
            return (head, None, name)
        # Venue-org suffixes strip before every dispatch below (operator,
        # pair, appositive, venue): the venue part names/locates.
        tail = self._strip_venue_org(tail)
        if (operator := self._slash_operator_pair(head, tail, name, segments)) is not None:
            return operator
        if (pair := self._resolve_slash_pair(head, tail, name)) is not None:
            return pair
        for noun in ("laituri", "ranta"):
            if tail.lower().endswith(noun) and noun in head.lower():
                # Appositive twins ("Linnanlaituri / Vesiliikennelaituri"):
                # the head already names it.
                self._count("name/slash_appositive")
                return head, None, name
        if not (self._has_fixture(head) or self._has_fixture(tail)):
            # No venue evidence on either side ("Aamulla / Vasikat"):
            # co-titles stay whole, never split into located_in.
            self._count("name/slash_venue_kept")
            return name, None, None
        self._count("name/slash_venue")
        return self._split_pair(head, tail, name, strict=True)

    def _resolve_nested(self, shown: str, located: str | None, official: str | None, name: str) -> SplitTriple:
        # Nested remainder ("Talin puttirata / Mini-Tali" naming a practice
        # area): resolve the inner pair for the name, preferring its venue.
        inner = self._split_slash(shown)
        if inner is not None and " / " not in inner[0]:
            self._count("name/slash_nested")
            return inner[0], inner[1] or located, official or name
        return shown, located, official

    def _split_machine(self, name: str) -> SplitTriple | None:
        # Ticket/vending machines carry address + payment metadata after
        # commas ("Pysäköintilippuautomaatti 222, Pengerkatu 23,
        # korttimaksu"): the machine + id names the POI, the rest survives
        # in official_name. Runs before the slash dispatch so embedded
        # slashes in the location note never mis-split.
        if "automaatti" not in name.lower() or "," not in name:
            return None
        head = self._comma_base(name)
        if not head or "automaatti" not in head.lower():
            return None
        self._count("name/comma_machine")
        return head, None, name

    def _split_paren(self, name: str, city: str | None) -> SplitTriple | None:
        # Trailing parentheticals are metadata or venues, never name parts.
        # Outermost group so nested coverage areas resolve as one
        # ("Eläinlääkäri (Aura, Pöytyä (Kyrö, Karinainen), ...)").
        if "(" not in name or not name.rstrip().endswith(")"):
            return None
        base, _, inner = name.partition("(")
        base, inner = base.strip(), inner.strip()
        if inner.endswith(")"):
            inner = inner[:-1].strip()
        if not base or not inner:
            return None
        if ") (" in inner or ")(" in inner:
            # Double parentheticals ("Kirjasto (Pääkirjasto) (Keskusta)"):
            # the trailing group drops; the base (carrying the first group)
            # re-dispatches so venue resolution runs on a clean shape.
            # The full form survives in official_name.
            outer, _, _trailing = name.rpartition("(")
            outer = outer.strip()
            self._count("name/paren_double_peeled")
            sub = self._split_paren(outer, city)
            if sub is None:
                return None
            return self._keep_official(sub, name)
        if (head := self._paren_head(base, inner, name, city)) is not None:
            return head
        if " / " in base and any(word in base.rsplit(" / ", 1)[1].strip().lower() for word in self.ROOM_WORDS):
            # Facility tails with parenthesised qualifiers ("...
            # / Ulkokuntoilupaikka (Keski)"): the slash dispatch names
            # the tailed facility, parens included — paren handling
            # would keep whole or strand the qualifier as the venue.
            return None
        return self._paren_tail(base, inner, name, city)

    def _paren_memorial(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if self._is_memorial(base, inner):
            self._count("name/paren_memorial")
            return name, None, None
        return None

    def _paren_slash_address(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if "/" in base and base.count("/") == 1 and self.COMMA_STREET_RE.search(inner.lower()):
            # A real venue name with a parenthesised address beats an
            # operator-shaped head ("Pilke päiväkodit Oy/
            # Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)").
            bhead, _, btail = base.rpartition("/")
            if btail.strip() and self._is_operator_shaped(bhead.strip()):
                self._count("name/slash_paren_address")
                return btail.strip(), None, name
        return None

    def _paren_head(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        # Memorials and slash venue-address pairs resolve before the
        # room-word deferral in the caller _split_paren.
        return self._first_hit((self._paren_memorial, self._paren_slash_address), base, inner, name, city)

    def _paren_coverage_sisters(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if (
            "," in inner
            and all(self._is_single_cap(seg) for seg in inner.split(","))
            and city
            and re.search(r",\s*" + re.escape(city.strip()) + r"\s*$", base, flags=re.IGNORECASE)
        ):
            # Coverage sisters after the municipality ("...Masku
            # (Nousiainen, Laitila)"): drop the list, re-split the base
            # so the city tail strips too. Runs before the venue branch:
            # room-word substrings ("tila" in Laitila) must not pose
            # municipalities as venues.
            self._count("name/paren_coverage_dropped")
            sub = self._split_name(base, city)
            return self._keep_official(sub, name)
        return None

    def _paren_coverage_city(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if (
            "," in inner
            and all(self._is_single_cap(seg) for seg in inner.split(","))
            and city
            and any(seg.strip().casefold() == city.strip().casefold() for seg in inner.split(","))
        ):
            # Coverage municipality lists containing the municipality
            # ("...Pohjatuuli (Karvia, ..., Kankaanpää, ...)"): the base
            # names the POI, the full form survives in official_name.
            self._count("name/paren_coverage_city_dropped")
            sub = self._split_name(base, city)
            return self._keep_official(sub, name)
        return None

    def _paren_venue_or_descriptor(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if self._has_no_digit(inner) and self._has_fixture(inner):
            # Venue in parens ("... (Oltermannikeskus)").
            if re.match(r"(yksityinen|kunnallinen)\b", inner.strip(), flags=re.IGNORECASE):
                # Generic type descriptors ("Touhula Helmiina (yksityinen
                # päiväkoti)") are not venues: strip to the base.
                sub = self._split_name(base, city)
                self._count("name/paren_descriptor_dropped")
                return self._keep_official(sub, name)
            self._count("name/paren_venue")
            return base, inner, name
        return None

    def _paren_numbered_room(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if (
            self._has_digit(inner)
            and self._has_fixture(inner)
            and not self.COMMA_STREET_RE.search(inner.lower())
            and not self.SUBUNIT_RE.search(inner.lower())
        ):
            # Numbered rooms/fields ("Kirjasto (Sali 2)"): the room names the
            # POI like slash rooms do; street addresses and ward/unit
            # qualifiers never qualify.
            self._count("name/paren_numbered_room")
            return self._split_pair(inner, base, name)
        return None

    def _paren_stripped_note(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if (
            self.COMMA_STREET_RE.search(inner.lower())
            or (self._has_digit(inner) and "," in inner)
            or "tekonurmi" in inner.lower()
            or "ajanvarau" in inner.lower()
            or inner.lower() in ("lakkautettu", "lakkautetaan", "väistö", "väistötila")
            or inner.lower().startswith("toiminta loppunut")
        ):
            # Street addresses, multi-municipality coverage areas, surface
            # notes ("...(hiekkatekonurmi)"), booking notes ("...(vain
            # ajanvarauksella)", stem-matched: the inflected form never
            # contains the nominative) and registry status notes
            # ("(lakkautettu)", "(väistö)") strip to the base.
            sub = self._split_name(base, city)
            self._count("name/paren_stripped")
            return self._keep_official(sub, name)
        return None

    def _paren_locality(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if self._is_single_cap(inner):
            # Single localities ("Totto-Halli (Muurola)") strip only when
            # they repeat known address context; village tails stay unless
            # they equal the municipality ("... (Idänpää)", Hämeenlinna).
            if city and inner.casefold() != city.strip().casefold():
                self._count("name/paren_village_kept")
                return name, None, None
            sub = self._split_name(base, city)
            self._count("name/paren_stripped")
            return self._keep_official(sub, name)
        return None

    def _paren_venue_list(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        if "," in inner and all(self._is_single_cap(seg) for seg in inner.split(",")):
            # Proper-name venue lists ("...(Masto, Styyrpuuri,Vantti)"):
            # the units locate the POI. Coverage cities stay whole, as do
            # lists on names without facility evidence.
            listed = ", ".join(seg.strip() for seg in inner.split(","))
            if not (city and any(s.strip().casefold() == city.strip().casefold() for s in inner.split(","))) and (
                self._has_fixture(base) or self._category(base)[0] is not None
            ):
                self._count("name/paren_venue_list")
                return base, listed, name
        return None

    def _paren_tail(self, base: str, inner: str, name: str, city: str | None) -> SplitTriple | None:
        # Coverage sisters, descriptors, stripped notes, localities and
        # venue lists resolve here; the room-word deferral runs first in
        # the caller _split_paren.
        hit = self._first_hit(
            (
                self._paren_coverage_sisters,
                self._paren_coverage_city,
                self._paren_venue_or_descriptor,
                self._paren_numbered_room,
                self._paren_stripped_note,
                self._paren_locality,
                self._paren_venue_list,
            ),
            base,
            inner,
            name,
            city,
        )
        if hit is not None:
            return hit
        # Short qualifiers (target groups, levels, "(ulko)") are part of
        # the signed service name and stay whole.
        self._count("name/paren_qualifier_kept")
        return name, None, None

    # Bare generic heads that are no venue for dash-room splits
    # ("Tila - Koskihalli" keeps whole).
    DASH_GENERIC_HEADS = frozenset(
        "tila keskus talo piste huone koppi katos kota laavu sali halli kenttä allas rata ".split()
    )

    def _dash_room(self, left: str, right: str, name: str) -> SplitTriple | None:
        if (
            self._has_fixture(left)
            and left.strip().lower() not in self.DASH_GENERIC_HEADS
            and "-" not in right
            and not re.match(r"(ja|tai|sekä|&)\b", right, flags=re.IGNORECASE)
            and any(tok.endswith(word) for tok in re.split(r"[\s-]+", right.lower()) for word in self.ROOM_WORDS)
        ):
            # Facility rooms as dash tails ("Pallokenttä - Sali 2"): the room
            # names the POI, the facility the venue (cf. slash rooms). Chained
            # and hyphenated tails, conjunction-led fragments
            # ("... - ja käsipallokenttä"), inflected lookalikes
            # ("... - potilaalle") and bare generic heads ("Tila - Koskihalli")
            # keep whole: room words read as whole tokens, never substrings,
            # and generic words are no venue.
            self._count("name/dash_room")
            return self._split_pair(right, left, name)
        return None

    def _dash_unit(self, left: str, right: str, name: str) -> SplitTriple | None:
        if re.search(
            r"(toimisto|kerho|ryhmä|klubi|piste|koulu|talo|keskus|asema|neuvonta|ohjaus|apteekki|kahvila)",
            right.lower(),
        ) and self._has_fixture(left):
            if re.search(r"(koulu(?!tus|tuk|lai)|lukio|opisto|skola)", right.lower()):
                # School-headed right sides ("Kaukajärven koulu - Annalan
                # koulutalo") are same-institution buildings, not hosted
                # units: keep whole rather than housing a school in itself.
                # Training/info units ("... - Koulutusinfo") are hosted
                # services, not schools: they split below.
                self._count("name/dash_school_kept")
                return None
            if re.search(r"(palvelu|toiminta)", left.lower()) and re.search(
                r"(toimisto|toimipiste|toimipaikka|piste|virasto)$", right.lower()
            ):
                # Service-org heads with office tails ("Luoteis-Savon
                # Maaseutupalvelut - Kiuruveden maataloustoimisto") name
                # one identity: keep whole (cf. Mänttä).
                self._count("name/dash_org_kept")
                return None
            self._count("name/dash_unit")
            return self._split_pair(self._cap_first(right), left, name)
        return None

    def _split_dash(self, name: str) -> SplitTriple | None:
        # Dash-separated venue/unit pairs ("Friemanin talo -
        # nuorisotoimisto"); translation dashes split earlier, lowercase
        # descriptors strip in cleaning.
        if " - " not in name:
            return None
        left, _, right = name.partition(" - ")
        left, right = left.strip(), right.strip()
        if not left or not right:
            return None
        return self._first_hit((self._dash_room, self._dash_unit), left, right, name)

    def _split_bare_desk(self, head: str, tail: str, tail_base: str, name: str) -> SplitTriple | None:
        # Bare desk tails on facility heads ("Vihdin kunnantalo/
        # sosiaalitoimisto", "Lohjan Kaupungintalo/
        # asiakaspalvelukeskus"): the desk names the POI. Role tails are
        # descriptors, not venues ("Rakennusvalvontatoimisto/
        # lupasihteeri"): keep the head. Desk words read as whole tokens:
        # districts ("Vihdin kunnantalo/Keskusta") and squares
        # (".../Keskustori") are not desks, while qualified desks
        # (".../Sote-keskus Länsi") still resolve.
        if (
            any(word in tail_base.lower() for word in ("toimisto", "toimipiste", "toimipaikka"))
            or re.search(r"(keskus|asema)(\s|$)", tail_base.lower())
        ) and self._has_fixture(head):
            self._count("name/slash_service_unit")
            return self._split_pair(tail, head, name)
        if re.fullmatch(r"\w*sihteeri", tail_base, flags=re.IGNORECASE):
            self._count("name/slash_role_dropped")
            return head, None, name
        return None

    def _bare_area_operator(self, head: str, tail: str, name: str) -> SplitTriple | None:
        # Area and operator heads resolve before service dispatch below.
        if head and tail and any(word in tail.lower() for word in self.AREA_TAILS):
            # Service areas ride bare slashes too ("Kotihoito/Vuosaari 3
            # lähipalvelualue"). Island areas locate instead of dropping.
            if self._island_area(tail):
                self._count("name/slash_area_island")
                return head, tail, name
            self._count("name/slash_area")
            return head, None, name
        if head and tail and any(word in head.lower() for word in self.AREA_TAILS):
            self._count("name/slash_area")
            return tail, None, name
        if head and tail and " " in head and self._is_operator_shaped(head):
            # Operator-headed records split regardless of tail spacing
            # ("Harjulan Setlementti ry/Liikuntapalvelut"). Venue/unit
            # tails name the POI instead (".../Kansalaisopisto",
            # ".../MyöhäTuulen kohtaamispaikka", ".../Villasukka");
            # bare service tails stay with the operator.
            if tail[:1].isupper() and self._is_venue_tail(tail):
                self._count("name/slash_operator_unit")
                return tail, None, name
            self._count("name/slash_operator_head")
            return head, None, name
        if head and tail and self._is_street_head(head):
            # Bare street heads are never venues either.
            self._count("name/slash_street_head")
            return tail, None, name
        return None

    def _bare_service_pair(self, head: str, tail: str, name: str) -> SplitTriple | None:
        # Genitive rooms, hosted units, desks and roles resolve before the
        # spaced-pair block below.
        if not (head and tail):
            return None
        tail_base = self._comma_base(tail)
        if re.search(r"(koulun|lukion|opiston|kodin)$", head.lower()) and self._is_room_tail(tail_base):
            # Genitive institution heads with room tails name one
            # facility ("Keuruun yläkoulun/lukion tanssisali"): keep
            # whole rather than strand a genitive fragment.
            self._count("name/slash_genitive_kept")
            return name, None, None
        if any(word in tail_base.lower() for word in self.SERVICE_TAILS) and self._has_fixture(head):
            # Hosted service units ("Töölön seniorikeskus/Helmi
            # ryhmäkoti"): the unit names the POI, the host the venue.
            # Bare desk tails count too ("Vihdin kunnantalo/
            # sosiaalitoimisto").
            self._count("name/slash_service_unit")
            return self._split_pair(tail, head, name)
        if (desk := self._split_bare_desk(head, tail, tail_base, name)) is not None:
            return desk
        return None

    def _split_bare(self, name: str) -> SplitTriple:
        # Bare slash: compounds without spaces stay whole (Geo/on),
        # hyphen fragments never split (hiekka-/jääkenttä).
        head, _, tail = name.rpartition("/")
        head, tail = head.strip(), tail.strip()
        if (area := self._bare_area_operator(head, tail, name)) is not None:
            return area
        if (service := self._bare_service_pair(head, tail, name)) is not None:
            return service
        spaced = self._bare_spaced_pair(head, tail, name)
        if spaced is self._BARE_DEFER:
            return None
        if spaced is not None:
            return spaced
        self._count("name/slash_kept")
        return name, None, None

    # Sentinel for "give up the bare-slash dispatch entirely" (comma
    # dispatch continues): distinct from None, which means "try the next
    # bare phase".
    _BARE_DEFER = object()

    def _bare_spaced_pair(self, head: str, tail: str, name: str) -> SplitTriple | None | object:
        # Pairs with spaces on both sides resolve last.
        if not (
            head
            and tail
            and " " in head
            and " " in tail
            and not head.endswith(("-", "/"))
            and not tail.startswith(("-", "/"))
            and len(head) > 1
            and len(tail) > 1
        ):
            return None
        if self._is_memorial(head, tail):
            self._count("name/slash_memorial")
            return name, None, None
        if self._is_operator_shaped(head):
            self._count("name/slash_operator_head")
            return head, None, name
        if self.COMMA_STREET_RE.search(tail.lower()) or any(word in tail.lower() for word in self.AREA_TAILS):
            self._count("name/slash_area")
            return head, None, name
        if any(word in head.lower() for word in self.AREA_TAILS):
            self._count("name/slash_area")
            return tail, None, name
        tail_base = self._comma_base(tail)
        if (
            "," in tail
            and self._is_single_cap(tail_base)
            and re.search(r"(puisto|keskus|halli|kenttä|stadion|areena|talo|koulu)$", head.lower())
        ):
            # Compound facility names ("...Keinupuisto/Hilpi,
            # Hämeenlinna, ..."): don't split the facility; comma
            # dispatch strips the city/service tails instead.
            return self._BARE_DEFER
        if not (self._has_fixture(head) or self._has_fixture(tail)):
            # No venue evidence on either side: co-titles stay whole.
            self._count("name/slash_venue_kept")
            return name, None, None
        self._count("name/slash_venue")
        return self._split_pair(head, tail, name, strict=True)

    def _is_venue_tail(self, tail: str) -> bool:
        # Venue/unit tails name the POI; bare service tails stay with the
        # operator. Service words strip first so "Palvelutalo" (venue)
        # doesn't read as a service ("Liikuntapalvelut" does).
        stripped = tail.lower()
        for word in self.SERVICE_TAILS:
            stripped = stripped.replace(word, "")
        return self._has_fixture(stripped) or not any(word in tail.lower() for word in self.SERVICE_TAILS)

    def _split_translation(self, signed: str) -> tuple[str, str] | None:
        # Bilingual dash names ("Bennäs Apotek - Pännäisten apteekki"):
        # the side without Swedish institution words names the POI.
        if " - " not in signed:
            return None
        left, _, right = signed.partition(" - ")
        left, right = left.strip(), right.strip()
        if not left or not right:
            return None
        if "palvelun järjestämis" in left or "palvelun järjestämis" in right:
            # Season-qualified service names ("... - Syksy 2026 -palvelun
            # järjestämispaikka") are not bilingual pairs; the normal path
            # strips the suffix and keeps the remainder whole.
            return None
        sw_l = bool(self.SWEDISH_WORD_RE.search(left))
        sw_r = bool(self.SWEDISH_WORD_RE.search(right))
        if sw_l == sw_r:
            return None
        if sw_l:
            return right, left
        return left, right

    # Swedish service tails for host<>facility inversion
    # ("Zacharias Topeliusskolan, Smågruppsundervisning").
    SWEDISH_SERVICE_TAILS = ("undervisning",)

    # Exact inessive venue stems ("Kuusankosken kirjastossa") shared by
    # _split_inessive and _custom_group_use.
    INESSIVE_HOST_STEMS = tuple(
        "kirjasto koulu lukio museo kirkko kappeli opisto sairaala neuvola päiväkoti päiväkodi terveysasema "
        "uimahalli nuorisotalo ".split()
    )

    def _split_inessive(self, name: str, tokens: list[str]) -> SplitTriple | None:
        # Services hosted AT a venue ("Martat neuvoo Kuusankosken
        # kirjastossa"): exact inessive venue nouns de-inflect to a
        # nominative located_in. Genitive-headed phrases stay whole.
        last = tokens[-1].lower()
        for stem in self.INESSIVE_HOST_STEMS:
            compound = re.fullmatch(r"(\w*?)" + stem + r"(ssa|ssä|lla|llä)", last)
            if compound is None:
                continue
            # Compound hosts ("pääkirjastossa") de-inflect like bare
            # ones; heads mixing genitives with a service word split
            # ("Lohjan Sydän digiopastusta"), pure genitive chains
            # ("Helsingin kaupungin") stay whole.
            host = compound.group(1) + stem
            venue_token = tokens[-2]
            head = " ".join(tokens[:-2])
            if (
                venue_token
                and venue_token[-1].lower() == "n"
                and head
                and not re.search(
                    r"\b\w*(koulu|lukio|opisto|päiväkoti|kirjasto|museo|kirkko|sairaala|neuvola)\b", head.lower()
                )
                and any(not t.lower().endswith("n") for t in head.split())
            ):
                self._count("name/inessive_host")
                return head, f"{venue_token} {host}", name
            break
        return None

    def _split_acronym_prefix(self, name: str) -> SplitTriple | None:
        if (m := re.match(r"(oysin|tyksin|husin|taysin|kysin)\s+(.+)$", name, flags=re.IGNORECASE)) and m.group(
            2
        ).strip():
            # Hospital acronym prefixes ("OYSin Keuhkosairauksien
            # poliklinikka"): the acronym operates the unit, never a venue,
            # so it strips off the name.
            self._count("name/acronym_prefix_dropped")
            return m.group(2).strip(), None, name
        return None

    def _split_slash_nested(self, name: str) -> SplitTriple | None:
        if (split := self._split_slash(name)) is not None:
            shown, located, official = split
            if " / " in shown:
                return self._resolve_nested(shown, located, official, name)
            return split
        return None

    def _split_name(self, name: str, city: str | None = None) -> SplitTriple:
        # Returns (name, located_in, official_name). Ordered precedence
        # table of (guard, resolver): guards keep resolvers from misfiring
        # on shapes they don't own (colons in URLs, acronym prefixes,
        # multi-slash chains); first non-None hit wins. Resolvers stay
        # lazy behind lambdas so a failed guard never calls them.
        tokens = name.split()
        for guard, resolver in (
            (True, lambda: self._split_machine(name)),
            (True, lambda: self._split_paren(name, city)),
            (True, lambda: self._split_dash(name)),
            (":" in name and "://" not in name, lambda: self._split_colon(name, city)),
            (True, lambda: self._split_acronym_prefix(name)),
            (len(tokens) >= 3, lambda: self._split_inessive(name, tokens)),
            (True, lambda: self._split_slash_nested(name)),
            # Bare-slash guards may decline (compound facilities): fall
            # through to comma shapes instead of stranding None.
            ("/" in name and name.count("/") == 1, lambda: self._split_bare(name)),
            (True, lambda: self._split_name_tail(name, city)),
        ):
            if guard and (split := resolver()) is not None:
                return split
        return name, None, None

    def _city_tail_stripped(self, text: str, city: str | None) -> str | None:
        # Trailing exact-municipality tails strip from service/facility heads
        # ("Fysioterapia Pori", "Kuntoutusohjaus Kankaanpää"): the city repeats
        # the structured address and would duplicate it. Brand-embedded cities
        # ("International House Rauma", "SavoGrow Pielavesi") keep the whole;
        # generic activity heads ("Avoin jumpparyhmä Kouvola") strip like
        # venues do; proper nouns keep the city. Shared by the space tail and
        # the comma service-head paths. Returns the stripped head, or None to
        # keep whole (callers fall through).
        if not city or " " not in text:
            return None
        head, _, tail = text.rpartition(" ")
        city_cf = city.strip().casefold()
        stripped_head = None
        if (
            head.strip()
            and tail
            and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+(?:-[A-ZÅÄÖ][a-zåäö-]+)?", tail)
            and tail.casefold() == city_cf
        ):
            stripped_head = head.strip()
        elif " " in city.strip() and text.lower().endswith(" " + city_cf):
            # Multiword municipalities ("X Koski Tl") never equal a single
            # tail token; match the whole tail instead.
            stripped_head = text[: -len(city.strip())].strip()
        if not stripped_head:
            return None
        if re.search(r"\b(of|av|de|von|van|di|da|le|la)$", stripped_head, flags=re.IGNORECASE):
            # The city completes a foreign proper name
            # ("International School of Helsinki"): stripping
            # leaves a dangling preposition, so keep the whole.
            self._count("name/space_city_kept")
            return None
        if (
            self._has_fixture(stripped_head)
            or self._category(stripped_head)[0] is not None
            or self._is_group_activity(stripped_head.lower())
        ):
            # Facility heads, categorized heads and generic group
            # heads ("Peliryhmä Kuopio") strip like venues do;
            # proper nouns keep the city.
            self._count("name/space_city")
            return stripped_head.rstrip("|/,").strip() or stripped_head
        if self._is_proper_tail(stripped_head) or (
            re.fullmatch(r"[A-ZÅÄÖ][A-Za-zåäö-]+", stripped_head) and not self._has_fixture(stripped_head)
        ):
            self._count("name/space_city_kept")
            return None
        self._count("name/space_city")
        return stripped_head.rstrip("|/,").strip() or stripped_head

    def _strip_service_city(self, split: SplitTriple, city: str | None, name: str) -> SplitTriple:
        # Comma service heads carrying an exact-city tail ("Fysioterapia Pori"
        # from a service@venue pair): strip by the same predicate as space
        # tails, keeping the venue. Comma-bearing shown forms (kept full
        # names) never enter: only bare service heads qualify.
        shown, located, official = split
        if "," not in shown and (stripped := self._city_tail_stripped(shown, city)) is not None:
            return stripped, located, official
        return split

    def _split_name_tail(self, name: str, city: str | None) -> SplitTriple | None:
        # Space-separated city tails, fused school heads
        # and comma shapes, in that precedence.
        if city and " " in name and "," not in name:
            # Space-separated city tails ("Kuntoutusohjaus Kankaanpää"):
            # the city repeats the structured address. No branch: it
            # would duplicate the city. Fused school heads re-dispatch so the
            # venue is not lost ("Renkomäen koulun luokat Lahti" names the
            # unit, the school locates it).
            if (stripped := self._city_tail_stripped(name, city)) is not None:
                if (fused := self._split_fused_school(stripped)) is not None:
                    return fused[0], fused[1], name
                return stripped, None, name
        if "," not in name and "/" not in name and ":" not in name:
            if (split := self._split_fused_school(name)) is not None:
                return split
        if "," in name:
            return self._split_comma(name, city)
        return None

    FUSED_ANCHORS = ("luokka", "luokat")

    def _split_fused_school(self, name: str) -> SplitTriple | None:
        # Comma-less "<Place-gen> <school-gen> <service/facility>" heads
        # ("Renkomäen koulun vaativan monimuotoisen tuen luokat"): the
        # unit names the POI, the school the venue. Anchored on service,
        # room and unit words so bare school phrases stay whole.
        tokens = name.split()
        if len(tokens) < 3:
            return None
        venue = None
        rest = ""
        for i in range(1, len(tokens) - 1):
            for genitive, nominative in self.SCHOOL_GENITIVE:
                if tokens[i].lower().endswith(genitive):
                    venue = " ".join(tokens[:i]) + " " + tokens[i][: -len(genitive)] + nominative
                    rest = " ".join(tokens[i + 1 :])
                    break
            if venue is not None:
                break
        if venue is None:
            return None
        if "(" in rest or ")" in rest:
            # Parenthesised qualifiers inside the unit ("... koulun (FISTA)
            # opiskeluhuolto") keep whole: parens are metadata or venues,
            # never name parts to strand.
            return None
        if re.match(r"\d", rest):
            # Numbered course fragments ("Kuivalahden koulun 5 -väyläinen
            # frisbeegolfrata") name one facility: keep whole rather than
            # strand a leading-number fragment.
            return None
        if re.match(r"(ja|tai|sekä|&)\b", rest, flags=re.IGNORECASE):
            # Joint schools ("Espoonlahden koulun ja lukion liikuntasali")
            # are one venue: keep whole rather than strand "Ja lukion".
            return None
        anchors = (*self.SERVICE_HEADS, *self.ROOM_WORDS, *self.SERVICE_TAILS, *self.FUSED_ANCHORS)
        if not rest or not any(word in rest.lower() for word in anchors):
            return None
        self._count("name/fused_school")
        return self._cap_first(rest), venue, name

    def _split_colon(self, name: str, city: str | None) -> SplitTriple | None:
        # City-first records ("Outokumpu: Vertaisryhmä...") name the tail;
        # operator tails strip to the head ("OLKA-pisteen teemapäivä:
        # Saimaan Syöpäyhdistys ry"). Colon branches ("...: Sampola")
        # stay whole here; _apply_branch files them (never for schools).
        head, _, tail = name.rpartition(":")
        head, tail = head.strip(), tail.strip()
        if not head or not tail:
            return None
        if city and head.casefold() == city.strip().casefold():
            self._count("name/colon_city_head")
            return tail, None, name
        if self._is_operator_shaped(tail):
            self._count("name/colon_operator_dropped")
            return head, None, name
        return None

    # Genitive institution nouns mapping to their nominative venue form
    # ("Rovastinkankaan koulun" -> "Rovastinkankaan koulu").
    SCHOOL_GENITIVE = (
        ("koulun", "koulu"),
        ("lukion", "lukio"),
        ("opiston", "opisto"),
        ("kodin", "koti"),
        ("talon", "talo"),
        ("asteen", "aste"),
    )

    def _genitive_school(self, head: str) -> str | None:
        # School part of a fused "<school-genitive> <service>" head; None
        # when the second-to-last token is no known institution noun.
        tokens = head.split()
        if len(tokens) < 2:
            return None
        last = tokens[-2]
        for gen, nom in self.SCHOOL_GENITIVE:
            if last.lower().endswith(gen):
                return " ".join(tokens[:-2] + [last[: -len(gen)] + nom])
        return None

    # Description keywords rescuing otherwise-unmapped opaque names
    # ("Naskali", whose description offers housing for the intellectually
    # disabled): housing + care reads as assisted living, care alone as a
    # plain social facility. Needs assessments never house anyone, so
    # assessment prose ("tarpeen arviointi") stays social. Rescue only,
    # never overrides a name mapping.
    CARE_HOUSING_RE = re.compile(r"asumi")
    NEEDS_ASSESSMENT_RE = re.compile(r"tarpee\w*\W+(?:\w+\W+){0,3}(arvio|selvitys|kartoitus)", re.IGNORECASE)
    CARE_WORDS = (
        "kehitysvamma",
        "vammais",
        "muistisairas",
        "dement",
        "mielenterveys",
        "päihde",
        "vanhus",
        "ikäänty",
        "lastensuojelu",
        "sijaishuolto",
        "lastenkoti",
    )

    ART_RE = re.compile(
        r"(veistos|patsas|taideteos|public art|artwork|skulptur|staty|\bkonst(när|verk)?\b)", re.IGNORECASE
    )

    def _description_text(self, channel: dict) -> str:
        # All languages joined: art is often documented only outside
        # Finnish ("Eino Leino is a work of public art"), while the
        # Finnish care vocabulary has no false friends abroad.
        return " ".join(
            (row.get("value") or "").lower()
            for row in channel.get("serviceChannelDescriptions") or []
            if isinstance(row, dict) and row.get("value")
        )

    # Supported-housing phrases: "tuettu" modifying housing, or 24-hour
    # residential wording, within a few words ("tuettua asumista",
    # "ympärivuorokautisen palveluasumisen"). Distant co-occurrence
    # across topics never counts (employment support beside housing stock).
    SUPPORTED_HOUSING_RE = re.compile(
        r"tuettu\w*\W+(?:\w+\W+){0,4}asumi|asumi\w*\W+(?:\w+\W+){0,4}tuettu"
        r"|ymp\xe4rivuorokautinen\W+(?:\w+\W+){0,4}asumi|asumi\w*\W+(?:\w+\W+){0,4}ymp\xe4rivuorokautinen",
        re.IGNORECASE,
    )

    def _supported_housing(self, channel: dict) -> bool:
        # Supported-housing evidence beats diagnosis (user doctrine):
        # each description, linked service and ontology value carries its
        # own topic, so the phrase must hold inside one string
        # ("Tervahovin asunnot"). Bare "asumi" alone never counts
        # (assessment offices).
        texts = [self._description_text(channel)]
        texts.extend(self._service_names(channel))
        texts.extend(self._ontology_names(channel))
        return any(self.SUPPORTED_HOUSING_RE.search(t or "") for t in texts)

    def _resolve_fallback_category(self, item: Feature, channel: dict) -> Categories | None:
        # Category for channels the name leaves generic: linked-service
        # and ontology rescue first, description rescue next, generic last.
        # Returns the resolved category (or None for extras-only rescue).
        rescued = self._rescue_service(channel)
        if rescued is None:
            category = self._rescue_category(channel)
            if category is None:
                self._count("category/unmapped")
                apply_category(Categories.GENERIC_POI, item)
            else:
                self._count("category/rescued/" + category.name)
                apply_category(category, item)
            return category
        if rescued[0] is None:
            # Placement-only rescue (zoo, youth centre): no POI
            # category, just the tags.
            for key, value in (rescued[1] or {}).items():
                item["extras"][key] = value
            self._count("category/rescued_service_extras")
            return None
        if rescued[0] == Categories.OFFICE_GOVERNMENT:
            # A desk label never shadows place evidence: descriptions
            # describing care or art win over the service desk.
            if (described := self._rescue_category(channel)) is not None:
                self._count("category/rescued/" + described.name)
                apply_category(described, item)
                return described
        self._count("category/rescued_service/" + rescued[0].name)
        apply_category(rescued[0], item)
        for key, value in (rescued[1] or {}).items():
            item["extras"][key] = value
        return rescued[0]

    # Service/ontology candidates that file as offices without naming a
    # desk ("Varhaiskasvatus", "tukipalvelut") are admin buckets, not
    # types: they never rescue, so the specific ontology behind them
    # ("päiväkotihoito") gets its chance. Desk-shaped office hits
    # ("erityislupa", "toimisto") rescue normally.
    RESCUE_ADMIN_SKIP = (
        "varhaiskasvatus",
        "tukipalvelu",
        "sosiaali",
        "neuvonta",
        "ohjaus",
        "toiminta",
        "hallinto",
        "liikuntapalvelu",
        "kiertotalouspalvelu",
    )

    # Placement-only extras that misfire from catalogue/service dumps:
    # shooting grounds (org sports catalogue on sled hills), cemeteries
    # (parish office desks), ticket shops (venues selling tickets) and
    # squares (market-rental services on town halls). Other placement tags
    # from real services (zoo shops, public art, youth centres) still rescue.
    RESCUE_PLACEMENT_SKIP = (
        ("leisure", "shooting_ground"),
        ("landuse", "cemetery"),
        ("shop", "tickets"),
        ("place", "square"),
    )
    ACTIVITY_RE = re.compile(
        # Event/activity nouns: care rescue describes their purpose, never
        # their type ("Nakkifiesta" with mental-health ontology stays generic).
        r"(verstas|fiesta|juhla|festivaali|karnevaali|kilpailu|turnaus|ottelu|konsertti|näytelmä|kurssi|leiri|tapahtuma)"
    )

    def _rescue_blocked(self, channel: dict) -> bool:
        # Names rescue never types: utility buildings (typed by hosted
        # services otherwise), fixed orienteering controls (typed by
        # shooting-ontology dumps otherwise), sled hills (typed by the
        # same sports-catalogue dumps; pulkkamäki has no enum and stays
        # generic by design), power plants (typed by wastewater-utility
        # dumps; no power-plant enum; bare Voimala venues and Voimalantie
        # streets never contain the plant stem) and shore paths (Rantaraitti is
        # a route, not a venue). All stay generic.
        fi = (self._names(channel).get("fi") or "").lower()
        return (
            "huoltorakennus" in fi
            or "kiintorasti" in fi
            or "pulkkam" in fi
            or "pulkbacke" in fi
            or "voimalaito" in fi
            or "rantaraitti" in fi
        )

    def _service_names(self, channel: dict) -> list[str]:
        # Channel-linked service names only (no org-catalogue ontology):
        # the island carve reads these, so catalogue "ulkoilusaaret" on
        # boat winter-storage areas never files islands.
        return [
            ((row or {}).get("service") or {}).get("name")
            for row in channel.get("services") or []
            if ((row or {}).get("service") or {}).get("name")
        ]

    def _ontology_names(self, channel: dict) -> list[str]:
        return [
            term_name["value"]
            for term in channel.get("ontologyTerms") or []
            if isinstance(term, dict)
            for term_name in term.get("name") or []
            if isinstance(term_name, dict) and term_name.get("language") == "fi" and term_name.get("value")
        ]

    def _rescue_candidates(self, channel: dict) -> list[str]:
        # Feed strings that can type an opaque channel, in precedence
        # order: linked services, ontology terms, translated names.
        candidates = []
        for row in channel.get("services") or []:
            name = ((row or {}).get("service") or {}).get("name")
            if name:
                candidates.append(name)
        candidates.extend(self._ontology_names(channel))
        for row in channel.get("serviceChannelNames") or []:
            # Translated names often type opaque Finnish ones ("Daghemmet
            # Karitsa" → kindergarten); untranslated copies fall through.
            if isinstance(row, dict) and row.get("language") not in ("fi", None):
                value = (row.get("value") or "").strip()
                if value:
                    candidates.append(value)
        return candidates

    def _rescue_service(self, channel: dict) -> tuple[Categories | None, dict | None] | None:
        # Linked PTV services and YSO ontology terms type opaque channels
        # ("Maya", "Coxa") from feed data. Rescue-tier only: the channel
        # name already failed, so the first non-generic hit wins. Admin
        # units ("Liikunnan ja urheilun tulosyksikkö") match nothing and
        # fall through to the description rescue below.
        if self._rescue_blocked(channel):
            return None
        candidates = self._rescue_candidates(channel)
        cleaned_fi_lower = self._clean_name(self._names(channel).get("fi") or "").lower()
        activity = self.ACTIVITY_RE.search(cleaned_fi_lower)
        peer = "vertais" in cleaned_fi_lower
        ward_name = self.SUBUNIT_RE.search(cleaned_fi_lower)
        if any(
            word in (c or "").lower()
            for c in self._service_names(channel)
            for word in ("ulkoilusaari", "ulkoilusaaret")
        ):
            # Outdoor-island channels ("Porsas" with Ulkoilusaaret
            # services) are islands, whatever the first service types.
            self._count("category/rescued_island")
            return None, {"place": "island"}
        if self._is_group_activity(cleaned_fi_lower):
            # Group-neutralized names carry no facility keyword: linked
            # services and catalogue ontology must not override the generic
            # verdict ("Laiturin Iloa"-groups with mental-health ontology
            # stay generic, never clinics; canteens never beat päiväkoti).
            return None
        for candidate in candidates:
            category, extra = self._category(self._clean_name(candidate))
            if extra == {"place": "island"}:
                # Islands ride along in translated names ("...explosionen
                # på Skanslandet..."); the Finnish name carries the tag.
                continue
            if activity and extra is None and category in (Categories.CLINIC, Categories.SOCIAL_FACILITY):
                continue
            if peer and extra is None and category == Categories.CLINIC:
                # Peer-delivered support ("Suvanto-vertaistiimi" with
                # mental-health ontology) is not a clinic; social rescue
                # below still applies.
                continue
            if "kartano" in cleaned_fi_lower and category == Categories.CARPET_WASHING:
                # Manor venues host laundry services; the manor is the POI.
                continue
            if category is not None and category != Categories.OFFICE_GOVERNMENT:
                # Specific types rescue; offices wait for the second pass so
                # a desk label never shadows a real type from a later
                # candidate ("päiväkotihoito" behind "Asiakaspalvelu").
                if category == Categories.HOSPITAL and ward_name:
                    # Ward-named channels ("Raaseporin TK vuodeosasto")
                    # are units, never hospitals, whatever the service.
                    return Categories.CLINIC, extra
                return category, extra
            if extra is not None and not any(extra.get(key) == value for key, value in self.RESCUE_PLACEMENT_SKIP):
                # Placement-only extras rescue too (zoo shops, public art),
                # except the catalogue-junk shapes (shooting grounds,
                # cemeteries, ticket shops, squares).
                return category, extra
        for candidate in candidates:
            # Second pass: desk-shaped office hits ("asiointipiste",
            # "toimisto") type opaque channels; generic admin labels
            # ("Varhaiskasvatus", "tukipalvelut") never do: the ontology
            # terms behind them ("päiväkotihoito") type the place better.
            if any(skip in candidate.lower() for skip in self.RESCUE_ADMIN_SKIP):
                continue
            category, extra = self._category(self._clean_name(candidate))
            if category == Categories.OFFICE_GOVERNMENT:
                return category, extra
        return None

    def _has_art_service(self, channel: dict) -> bool:
        # Public-art evidence in linked services/ontology ("Julkinen
        # taide", "veistokset"): artworks titled like islands still file
        # as art. Bare-"Saari" names only; island-proper names keep land.
        if self._clean_name((self._names(channel).get("fi") or "")).lower() != "saari":
            return False
        for row in channel.get("services") or []:
            name = ((row or {}).get("service") or {}).get("name") or ""
            if "taide" in name.lower() or "veistos" in name.lower() or "museo" in name.lower():
                return True
        return any(w in v.lower() for v in self._ontology_names(channel) for w in ("taide", "veistos", "museo"))

    def _rescue_category(self, channel: dict) -> Categories | None:
        text = self._description_text(channel)
        if not text:
            return None
        if self._rescue_blocked(channel):
            # Utility buildings and orienteering controls stay generic
            # whatever the description says.
            return None
        if self.ART_RE.search(text):
            # Documented public art wins over institutional history
            # ("K17" art space in a former psychiatric-hospital greenhouse
            # mentions both; the art space is the POI).
            return Categories.TOURISM_ARTWORK
        if re.search(r"(psykiatr|poliklinikk)", text):
            # Psychiatric outpatient units ("Tays Hallituskatu") are
            # clinics, not social facilities.
            return Categories.CLINIC
        if re.search(r"(kiireellis|akuutti)", text):
            # Urgent-care desks ("Päivystyksellinen kuulokojehuolto")
            # are urgent clinics. Plain on-call duty ("päivystys" at
            # utilities, weekly volunteers) is not urgency.
            return Categories.CLINIC_URGENT
        if any(word in text for word in self.CARE_WORDS):
            if self.CARE_HOUSING_RE.search(text) and not self.NEEDS_ASSESSMENT_RE.search(text):
                return Categories.ASSISTED_LIVING
            return Categories.SOCIAL_FACILITY
        return None

    def _split_comma_street_head(self, head: str, tail: str, name: str, city: str | None) -> SplitTriple | None:
        # Street+municipality heads ("Pyhämäntie, Janakkala, Vammaisten
        # asumispalvelut"): the service tail names the POI. Length-guarded
        # like street tails; locality heads ("Toivakka, Lapua") stay whole.
        if not city or "," not in head:
            return None
        m = re.match(r"^(.*?),\s*([^,]+)$", head)
        if m is None or m.group(2).strip().casefold() != city.strip().casefold():
            return None
        if len(m.group(1).strip()) < 7:
            return None
        if not re.search(r"(" + self.STREET_STEM_ALT + r")$", m.group(1).strip().lower()):
            return None
        self._count("name/comma_street_head")
        return tail, None, name

    def _split_comma_tail(self, head: str, tail: str, name: str, city: str | None) -> SplitTriple | None:
        # Metadata and coverage tails resolve before venue dispatch.
        # Returns None to fall through to street/city/service handling.
        if self._is_memorial(head, tail):
            self._count("name/comma_memorial")
            return name, None, None
        if "keskitetty" in name.lower():
            # Centralized services ("Opiskeluterveydenhuolto,
            # keskitetty palvelu Espoo ja Kauniainen") describe
            # coverage, not a host venue: the signed form stays
            # whole, never split into located_in.
            self._count("name/comma_centralized_kept")
            return name, None, None
        if self._is_operator_shaped(tail):
            # Maintainer tails are operators, not venues
            # ("Torpparinmäen peruskoulu, Puuhala Oy").
            self._count("name/comma_operator_dropped")
            return head, None, name
        if self.COMMA_STREET_RE.search(tail.lower()):
            self._count("name/comma_address_dropped")
            return head, None, name
        if any(word in tail.lower() for word in self.AREA_TAILS):
            if self._island_area(tail):
                self._count("name/comma_area_island")
                return head, tail, name
            self._count("name/comma_area")
            return head, None, name
        if re.match(r"mm\.", tail, flags=re.IGNORECASE):
            # Coverage remainder ("Lastensuojelun jälkihuolto, mm.
            # Iisalmi"): the "among others" tail drops.
            self._count("name/comma_mm_dropped")
            return head, None, name
        if (
            name.count(",") >= 2
            and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+(?:-[A-ZÅÄÖ][a-zåäö-]+)?", tail)
            and (not self._has_fixture(tail) or name.count(",") >= 3 or tail.strip().casefold() in self.MUNICIPALITIES)
        ):
            # Multi-municipality coverage lists ("Kuntoutusohjaus,
            # Kaarina, Lieto, ..."): peel trailing towns and keep
            # peeling; the full form survives in official_name. Mid-list
            # fixture towns ("...Pyhäranta, Raisio...") peel too: a venue
            # tail ends the list, never continues it. Gazetteer towns peel
            # even mid-list ("..., Kustavi, Laitila, ..."): exact matching
            # beats the fixture substring ("tila" in Laitila), so all
            # trailing municipalities pop in one pass, then the remainder
            # re-dispatches exactly as before. Single-town names ("Ravintola,
            # Lahti") never enter: the count guard protects them.
            parts = [s.strip() for s in name.split(",")]
            towns = 0
            while (
                len(parts) >= 2
                and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+(?:-[A-ZÅÄÖ][a-zåäö-]+)?", parts[-1])
                and parts[-1].strip().casefold() in self.MUNICIPALITIES
            ):
                parts.pop()
                towns += 1
            if towns:
                self._count("name/comma_coverage_list", towns)
                if len(parts) == 1:
                    return parts[0], None, name
                sub = self._split_comma(", ".join(parts), city)
                return self._keep_official(sub, name)
            self._count("name/comma_coverage_list")
            sub = self._split_comma(head, city)
            return self._keep_official(sub, name)
        return None

    def _comma_tail_pre(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Metadata tails and bare street tails dispatch before mid below.
        if (tail_hit := self._split_comma_tail(head, tail, name, city)) is not None:
            return tail_hit
        if len(tail) >= 7 and re.search(r"(" + self.STREET_STEM_ALT + r")$", lowered_tail):
            # Bare street tails are addresses, never venues
            # ("Kouluravintola, ..., Kenttäpolku"). Length-guarded:
            # short names ("Stig") are not streets.
            self._count("name/comma_street_tail")
            return head, None, name
        return None

    def _comma_city_police(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # City tails, street heads and inflected coverage dispatch before
        # the service split below. Lowered forms unused here (case-sensitive
        # tail shapes); kept for the uniform resolver signature.
        if city and tail.casefold() == city.strip().casefold():
            # The tail repeats the structured post office
            # ("Kiikoisten lähitori, Sastamala").
            self._count("name/comma_city")
            return head, None, name
        if (street_head := self._split_comma_street_head(head, tail, name, city)) is not None:
            return street_head
        if re.fullmatch(r"[A-ZÅÄÖ][\w.-]*:?(lla|llä|ssa|ssä|sta|stä|lta|ltä)", tail) and not self._has_fixture(tail):
            # Inflected place-name tails are coverage ("..., K-U:lla"),
            # not venues.
            self._count("name/comma_coverage_inflected")
            return head, None, name
        return None

    def _comma_site_recurse(
        self, head: str, tail: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Double-comma site qualifiers ("Kouluravintola, ... koulu,
        # ... toimipiste"): resolve the head, the tail rides into located_in.
        if "," in head and re.search(r"(toimipiste|toimipaikka|sivukoulu|enhet)", lowered_tail):
            sub = self._split_comma(head, city)
            if sub[1] is not None:
                self._count("name/comma_site_tail")
                return sub[0], sub[1] + ", " + tail, name
        return None

    def _split_comma(self, name: str, city: str | None = None) -> SplitTriple:
        head, _, tail = name.rpartition(",")
        head, tail = head.strip(), tail.strip()
        if head and tail and city:
            city_lead = re.match(re.escape(city.strip()) + r"\s+[–—-]\s+(.*)$", tail, flags=re.IGNORECASE)
            if city_lead and city_lead.group(1).strip():
                # Comma tails leading with the municipality ("Avustajakurssi,
                # Pori - vapaaehtoistoimintaan mukaan!"): peel the city, the
                # remainder dispatches as the tail.
                self._count("name/comma_city_lead")
                tail = city_lead.group(1).strip()
        if head and tail:
            lowered_tail = tail.lower()
            lowered_head = head.lower()
            # Ordered precedence table: metadata → hosted-unit/city →
            # city-police → service split. First non-None hit wins; total
            # misses keep the whole (this method never returns None).
            hit = self._first_hit(
                (
                    self._comma_tail_pre,
                    self._split_comma_mid,
                    self._comma_city_police,
                    self._split_comma_service_wrapped,
                ),
                head,
                tail,
                lowered_head,
                lowered_tail,
                name,
                city,
            )
            if hit is not None:
                if hit[1] is None:
                    if (site := self._comma_site_recurse(head, tail, lowered_tail, name, city)) is not None:
                        return site
                return hit
            if (site := self._comma_site_recurse(head, tail, lowered_tail, name, city)) is not None:
                return site
            # Bare city tails and appositive descriptors stay whole:
            # the structured address carries the city.
            self._count("name/comma_kept")
            return name, None, None
        if head and not tail:
            # Dangling comma ("Neuvonta,"): the head names it, the signed
            # form survives in official_name.
            self._count("name/comma_dangling")
            return head, None, name
        return name, None, None

    def _split_comma_service_wrapped(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Service split plus exact-city tail strip on bare service heads;
        # wrapped so the top-level precedence table stays uniform.
        if (service := self._split_comma_service(head, tail, lowered_head, lowered_tail, name, city)) is not None:
            return self._strip_service_city(service, city, name)
        return None

    def _comma_unit(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if any(word in lowered_tail for word in self.UNIT_TAILS) and self._is_institution(head.lower()):
            self._count("name/comma_unit")
            return self._split_pair(tail, head, name, strict=True)
        return None

    def _comma_branch_kept(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if any(word in lowered_tail for word in self.BRANCH_TAILS):
            # Campus/desk qualifiers are part of the signed name
            # ("Stadin ammattiopisto, Roihupellon toimipaikka"): OSM
            # branch=* is chain-retail with brand=*, not schools, and
            # the short form is not derivable without morphology, so
            # the full form stays the name (cf. way/1094085495).
            self._count("name/comma_branch_kept")
            return name, None, None
        return None

    def _comma_school_health_service(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if tail.lower() in self.SERVICE_HEADS and re.search(r"(koulu|lukio|opisto)", lowered_head):
            # School-hosted health services ("Merilahden peruskoulu,
            # Jaluspolun toimipiste, kouluterveydenhuolto"): the service
            # names the POI, the school hosts it (cf. service@school).
            self._count("name/comma_school_health_service")
            shown = self._cap_first(tail)
            return self._split_pair(shown, head, name)
        return None

    def _comma_room(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if tail.strip().casefold() in self.MUNICIPALITIES:
            # Municipality tails are cities, never rooms ("Perheneuvola,
            # Laitila", "Laitilan terveysasema, Laitila"): the room
            # substring ("tila" in Laitila/Marttila/Orimattila, the only
            # such municipalities) must not invert service@city rows.
            # Falls through to the city-tail rules below.
            return None
        if self._is_room_tail(lowered_tail) and self._is_institution(head.lower()):
            # Facility rooms/fields at institutions ("Vaajakummun koulu,
            # luistelukenttä"): the room names the POI (cf. slash_room).
            self._count("name/comma_room")
            return self._split_pair(tail, head, name, strict=True)
        return None

    def _comma_city_head(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if city and any(head.casefold() == part.strip().casefold() for part in city.split(" - ")):
            # City-first records ("Vaasa, Ulosottolaitos"); bilingual
            # post-office cities match either form ("Maarianhamina" of
            # "Maarianhamina - Mariehamn").
            self._count("name/comma_city_head")
            return tail, None, name
        return None

    def _comma_service_venue(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if self._endswith_any(lowered_head, self.SERVICE_HEADS) and self.SCHOOL_TAIL_RE.search(tail.lower()):
            self._count("name/comma_service_venue")
            return self._split_pair(head, tail, name, strict=True)
        return None

    def _comma_service_genitive(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if self._endswith_any(lowered_head, self.SERVICE_HEADS):
            # Fused genitive shape ("Rovastinkankaan koulun
            # opiskeluhuolto, Orivesi"): the service names the POI,
            # the school is the venue (cf. the service-map
            # school-head/service-tail rule, word order inverted).
            if (venue := self._genitive_school(head)) is not None:
                self._count("name/comma_service_genitive")
                return head.split()[-1].capitalize(), venue, name
        return None

    def _split_comma_mid(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Hosted-unit, branch-qualifier, city-first and service-head
        # comma pairs. Returns None to fall through to city tails and
        # the service split.
        return self._first_hit(
            (
                self._comma_branch_site,
                self._comma_unit,
                self._comma_branch_kept,
                self._comma_school_health_service,
                self._comma_room,
                self._comma_city_head,
                self._comma_service_venue,
                self._comma_service_genitive,
            ),
            head,
            tail,
            lowered_head,
            lowered_tail,
            name,
            city,
        )

    def _comma_branch_site(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Branch sites of branch-carrying institutions ("Vantaan
        # musiikkiopisto, Patotien pääopetuspiste"): the institution
        # names the POI, the site becomes branch below. Hosted units
        # ("... koulun opetuspiste", "... päiväkodin opetuspiste",
        # "... opistotalon ... opetuspiste") keep their venue filing.
        if (
            head.lower().endswith("musiikkiopisto")
            and "opetuspiste" in tail.lower()
            and not re.search(r"(koulu|skola|opisto|päiväkoti|päiväkodi)", tail.lower())
        ):
            self._count("name/comma_branch_site")
            return head, None, name
        return None

    def _split_comma_school_host(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Group activities hosted at schools ("Lempeä selkäjooga-ryhmä,
        # Veittijärven koulu"): the school locates the activity instead
        # of typing it. Daycare hosts stay whole (the daycare is the venue).
        # City unused; kept for the uniform resolver signature.
        if (
            self.SCHOOL_HOST_TAIL_RE.search(lowered_tail)
            and self._custom_group_use(head, lowered_head) is not None
            and not self.SCHOOL_HOST_RE.search(lowered_head)
        ):
            self._count("name/comma_school_host")
            return self._split_pair(head, tail, name)
        return None

    # Service words shared by head and tail: the tail redescribes the head's
    # own service ("Ilveskodin päivätoiminta, Vammaisten päivätoiminta"),
    # never a separate venue.
    def _shared_service_word(self, head: str, tail: str) -> bool:
        head_words = {t.strip(",.;:") for t in head.lower().split()}
        return any(word in head_words for word in self.SERVICE_TAILS if word in tail.lower())

    def _comma_pair_eligible(self, head: str, tail: str) -> bool:
        # Guard shared by the comma service-head and unit-venue splits:
        # the tail must not redescribe the head's own service, and bare
        # unit qualifiers split only against venue heads (cf. Stadin).
        return (
            not self._shared_service_word(head, tail)
            and (not self._is_unit_tail(tail) or self._is_venue_head(head))
            and (not self._is_unit_tail(head) or self._is_venue_head(tail))
        )

    def _split_comma_service_head(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Service-headed pairs ("Perhekeskus, Suvituuli") and hospital
        # wards ("Raskauden seurantaosasto, Tyks Majakkasairaala"): the
        # head names the POI, the venue hosts it (wards cf.
        # comma_service_unit for yksikkö units). Lowercase service tails
        # without institution words or proper nouns drop instead
        # (descriptor branch below). City unused; kept for the uniform
        # resolver signature.
        if (
            any(word in lowered_head for word in self.SERVICE_TAILS)
            and self._has_fixture(tail)
            and "," not in head
            and self._comma_pair_eligible(head, tail)
            and (tail[:1].isupper() or self.CORE_INSTITUTION_RE.search(lowered_tail) or re.search(r"\s[A-ZÅÄÖ]", tail))
        ):
            self._count("name/comma_service_unit")
            shown = self._cap_first(head)
            return self._split_pair(shown, tail, name, strict=True)
        if re.search(r"\w*(osasto|päiväsairaala)$", lowered_head) and re.search(
            r"(sairaala|terveyskeskus|terveysasema|mielenterveyskeskus)$", lowered_tail
        ):
            self._count("name/comma_ward_venue")
            return self._split_pair(head, tail, name)
        return None

    def _split_comma_unit_venue(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Venue-headed service pairs ("Perhekeskus, Suvituuli"): the tail
        # service names the POI, the venue head hosts it.
        if (
            any(word in lowered_tail for word in self.SERVICE_TAILS)
            and (self._has_fixture(head) or (self._is_proper_tail(head) and not self._is_person(head)))
            and self._comma_pair_eligible(head, tail)
            and not re.search(r"\b(oy|ab)\b", head, flags=re.IGNORECASE)
            and not self._is_private_org(head)
        ):
            self._count("name/comma_unit_venue")
            shown = self._cap_first(tail)
            # City-carrying venue heads resolve ("Kivari, Riihimäki");
            # multi-venue heads without one ("Riihikoti, Villava") stay whole.
            located = self._locate_venue_head(head, city)
            return shown, located or head, name
        return None

    def _locate_venue_head(self, head: str, city: str | None) -> str | None:
        # Venue heads carrying their own city tail resolve through the
        # comma dispatch ("Kivari, Riihimäki" → Kivari); multi-venue
        # heads without a resolvable city ("Riihikoti, Villava") stay whole.
        if "," not in head:
            return self._located_or(head)
        sub = self._split_comma(head, city)
        if sub[1] is None and sub[0] != head:
            return sub[0]
        return head

    def _split_comma_keep_whole(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Coverage areas and organisation desks keep the signed form whole,
        # never split into located_in (cf. Stadin, police desks). City unused;
        # kept for the uniform resolver signature.
        if self._is_bare_area(head) or self._is_bare_area(tail):
            # Bare coverage areas ("Puheterapia, Tikkurilan alue").
            self._count("name/comma_area_kept")
            return name, None, None
        if self._endswith_any(lowered_tail, ("vastaanotto",)) and self._endswith_any(
            lowered_head, ("toimisto", "virasto", "kaupunki", "kunta")
        ):
            # Desks of offices and municipalities ("Pirkanmaan
            # oikeusaputoimisto, Valkeakosken vastaanotto"): the
            # organisation is not a venue.
            self._count("name/comma_office_desk_kept")
            return name, None, None
        return None

    def _comma_leisure_house(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if re.search(r"vapaa-aika ?talo$", lowered_tail) and self._has_fixture(head):
            # Leisure-house venues ("Kuntosali, Kaukajärven vapaa-aika
            # talo"): the service/room head names the POI, the house
            # hosts it.
            self._count("name/comma_leisure_house")
            return self._split_pair(head, tail, name)
        return None

    def _comma_shared_redundant(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if self._shared_service_word(head, tail) and not self._is_proper_tail(tail):
            # Service-descriptor tails restating the head's own service
            # ("Ilveskodin päivätoiminta, Vammaisten päivätoiminta"): the
            # head names it; middle-city segments strip with it.
            self._count("name/comma_service_redundant")
            if city:
                head = re.sub(r",\s*" + re.escape(city.strip()) + r"(?=\s*,|\s*$)", "", head).strip()
            return head, None, name
        return None

    def _split_comma_service(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Service/unit comma pairs, both directions, then tail cleaners.
        hit = self._first_hit(
            (
                self._split_comma_keep_whole,
                self._split_comma_school_host,
                self._comma_leisure_house,
                self._comma_shared_redundant,
                self._split_comma_service_head,
                self._split_comma_unit_venue,
            ),
            head,
            tail,
            lowered_head,
            lowered_tail,
            name,
            city,
        )
        if hit is not None:
            return hit
        return self._split_comma_tail_rest(head, tail, lowered_head, lowered_tail, name, city)

    def _comma_sv_service(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if any(word in lowered_tail for word in self.SWEDISH_SERVICE_TAILS) and self._is_institution(lowered_head):
            # Swedish service tails ("Zacharias Topeliusskolan,
            # Smågruppsundervisning"): the service names the POI.
            self._count("name/comma_unit_venue_sv")
            return self._split_pair(tail, head, name)
        return None

    def _comma_unit_proper(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if self._is_single_cap(tail) and self._is_institution(lowered_head):
            if re.search(r"(koulu|lukio|opisto|päiväkoti|esiopetus|yläaste|ala-aste|skola|daghem)", lowered_head):
                # Named units hosted at schools ("Sipoon lukio, Enter").
                # Localities at other institutions ("Kalvolan neuvola,
                # Iittala") stay whole: no gazetteer distinguishes them.
                self._count("name/comma_unit_proper")
                return self._split_pair(tail, head, name)
            self._count("name/comma_unit_locality_kept")
            return name, None, None
        return None

    def _comma_proper_venue(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if self._is_single_cap(tail) and self._has_fixture(tail):
            # Named venues host the head service ("Neuvonta, Reimasali").
            self._count("name/comma_proper_venue")
            return self._split_pair(head, tail, name, strict=True)
        return None

    def _comma_water_venue(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if (
            self._is_single_cap(tail)
            and tail.lower().endswith(("järvi", "lampi", "saari", "luoto", "joki", "koski"))
            and self._has_fixture(head)
        ):
            # Lakes and waters name venues ("Vojakkalan uimapaikka,
            # Kaartjärvi"): the facility names the POI, the water hosts it.
            self._count("name/comma_water_venue")
            return self._split_pair(head, tail, name)
        return None

    def _comma_acronym_dropped(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if len(tail) >= 3 and tail.upper() in self.HOSPITAL_ACRONYMS:
            # Hospital acronym tails operate the unit ("... osasto J1,
            # Tyks"): the tail strips off the name, never a venue.
            self._count("name/comma_acronym_dropped")
            return head, None, name
        return None

    def _comma_facility_venue(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if (
            self._has_fixture(head)
            and self._is_proper_tail(tail)
            and re.search(
                r"(puisto|koulu|kirjasto|museo|kirkko|kappeli|tori|kenttä|ranta|satama|asema"
                r"|lukio|opisto|päiväkoti)",
                lowered_tail,
            )
        ):
            # Facilities at proper-named venues ("Kahluuallas, Leikkipuisto
            # Traktori"): the facility names the POI (cf. slash_room).
            self._count("name/comma_facility_venue")
            return self._split_pair(head, tail, name, strict=True)
        return None

    def _comma_tail_proper(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Swedish tails, proper/unit/water/facility venues and acronym strips.
        return self._first_hit(
            (
                self._comma_sv_service,
                self._comma_unit_proper,
                self._comma_proper_venue,
                self._comma_water_venue,
                self._comma_acronym_dropped,
                self._comma_facility_venue,
            ),
            head,
            tail,
            lowered_head,
            lowered_tail,
            name,
            city,
        )

    def _comma_tail_coverage(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Coverage lists, ward qualifiers and lowercase descriptors.
        # Only head/tail/name read; the rest kept for the uniform signature.
        if " ja " in tail and not self._has_fixture(tail) and self._has_no_digit(tail):
            swept = re.sub(r"\b(ja|och|eller|tai|sek\xe4)\b", "", tail, flags=re.IGNORECASE)
            if re.search(r"(?:^|\s)[a-zåäö]{3,}", swept) and not re.fullmatch(
                r"(?:iltaisin|aamuisin|p\xe4ivisin|\xf6isin|viikonloppuisin|viikonloppuina|arkisin|arkipyhin\xe4"
                r"|pyhin\xe4|pyhisin|lomilla|kes\xe4isin|talvisin|aamuin|illoin|\xf6in|[\s,]+)*",
                swept.strip(),
                flags=re.IGNORECASE,
            ):
                # Content words beyond places ("kahvetta ja kastamista
                # Kiikassa"): event program, not a coverage list. Bare
                # place lists ("Oulainen ja Merijärvi") and pure opening-time
                # lists ("iltaisin, viikonloppuina ja arkipyhinä") still drop.
                return None
            if head.rstrip().endswith("-"):
                # Hyphen-fragment lists ("Sovellettua jooga-, pilates- ja
                # faskiaharjoittelua") are one name, not coverage areas.
                return None
            # Municipality-coverage tails ("Kotihoito, Oulainen ja Merijärvi").
            self._count("name/comma_coverage_dropped")
            return head, None, name
        return None

    def _comma_tail_descriptor(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if (
            tail
            and tail[0].islower()
            and any(word in lowered_tail for word in ("palvelu", "toiminta", "hoito", "huolto", "työ", "tuki"))
            and not self.CORE_INSTITUTION_RE.search(lowered_tail)
        ):
            # Lowercase service descriptors ("Teuvolan vammaisten
            # asumispalvelut, tilapäishoito ja loma-ajanhoito"): the head
            # names it, the tail is no venue. Comma heads resolve further
            # ("Ikifit Oy, ...Keinupuisto/Hilpi, Hämeenlinna, ...").
            self._count("name/comma_descriptor_dropped")
            if "," in head:
                sub = self._split_comma(head, city)
                return self._keep_official(sub, name)
            return head, None, name
        return None

    def _comma_ward_kept(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if re.fullmatch(r"osasto\s*\d+\.?$", tail, flags=re.IGNORECASE):
            # Ward qualifiers are part of the signed name ("Katriinan
            # toimipiste, osasto 7", cf. the round-14 ward split): keep
            # whole, never strand the department number.
            self._count("name/comma_ward_kept")
            return name, None, None
        return None

    def _comma_tail_descriptor_bare(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        if (
            tail
            and tail[0].islower()
            and any(word in tail.lower() for word in ("palvelu", "toiminta", "hoito", "huolto", "työ", "tuki"))
        ):
            # Lowercase service descriptors ("..., ostopalvelut", "Novida,
            # lukion opiskeluhuolto"). Other lowercase tails (qualifiers
            # like "åk 1–2") stay whole.
            self._count("name/comma_descriptor_dropped")
            return head, None, name
        return None

    def _split_comma_tail_rest(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> SplitTriple | None:
        # Lowercase descriptors, Swedish tails, proper/unit venues and
        # coverage tails resolve after the service/unit dispatch above.
        return self._first_hit(
            (
                self._comma_tail_descriptor,
                self._comma_tail_proper,
                self._comma_tail_coverage,
                self._comma_ward_kept,
                self._comma_tail_descriptor_bare,
            ),
            head,
            tail,
            lowered_head,
            lowered_tail,
            name,
            city,
        )

    PHONE_HINT_RE = re.compile(r"(puhelin|phone|telefon)", re.IGNORECASE)
    ZW_RE = re.compile("[\u200b-\u200d\ufeff\u00ad]")
    # Switchboard/central contacts stamped across locations are not
    # per-store data (cf. the JSON-LD hotline lesson): drop on sight.
    # Canonical national-significant digits (country 358 and trunk 0
    # stripped, so +358/09/no-prefix feed shapes all match). Audited
    # 2026-10-14: each spans locations citywide or nationally (row counts
    # are raw locations sharing the number): Helsinki central 09 310 22111
    # (609, 3 departments), Espoo bulk 09 816 25100 (247, incl. parks),
    # Helsinki 09 310 1691 (201, 3 departments), Vantaa 09 839 22242
    # (198, incl. schools), police national permit line 0295 419 800
    # (139, 11 departments), Varha 02 313 2200/2100 (rows keep alternates),
    # Kotka 05 23480 (95, incl. beaches), HUS lab central 09 4718 6800
    # (92), medical helpline 116117 (90, 7 orgs), RIKU helpline 116006
    # (23, leaves RIKU points phoneless by design), Pori vaihde
    # 02 621 1100 (77), Turku vaihde 02 330 000, HUS vaihde 09 4711,
    # Raahe employment 08 439 4000/1 (rows keep alternates), Tyks main
    # 02 313 0000 (33), Ulosotto 0295 658 800 (rows keep alternates).
    # Round-24 fallback review: Ulosotto 0295 658 807/801 share across
    # 12+ cities nationwide (Espoo–Kouvola), and bare 112 (the national
    # emergency code, emitted on 5 päivystys rows) is never a unit number.
    GENERIC_PHONES = frozenset(
        {
            "981621",
            "983911",
            "931022111",
            "981625100",
            "93101691",
            "983922242",
            "295419800",
            "23132200",
            "23132100",
            "523480",
            "947186800",
            "116117",
            "116006",
            "26211100",
            "2330000",
            "94711",
            "84394000",
            "84394001",
            "23130000",
            "295658800",
            "295658807",
            "295658801",
            "112",
        }
    )
    GENERIC_EMAILS = frozenset({"info@esperi.fi"})  # Central corporate inbox
    LOGIN_URL_RE = re.compile(
        r"(authentication|/login|login[./?#]|log-in|sso[.-]|idp[-.]|menu\.|safelinks|@)", re.IGNORECASE
    )

    @classmethod
    def _visible(cls, text: str) -> str:
        return cls.ZW_RE.sub("", text)

    def _entry_is_phone(self, entry: dict) -> bool:
        for row in entry.get("additionalInformation") or []:
            if isinstance(row, dict) and self.PHONE_HINT_RE.search(row.get("value") or ""):
                return True
        return False

    @staticmethod
    def _to_minutes(value: str | None) -> int | None:
        # HH:MM with optional :SS (feed uses HH:MM:SS): prefix junk
        # ("08:00-12:00" in one field) and impossible hours ("25:00") drop
        # instead of silently truncating into invalid opening_hours.
        match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", (value or "").strip())
        if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
            return None
        if match.group(3) is not None and int(match.group(3)) > 59:
            # Feed seconds are real ("10:00:99" is junk, not 10:00).
            return None
        return int(match.group(1)) * 60 + int(match.group(2))

    def _merge_spans(self, spans: list[list[int]]) -> list[tuple[int, int]]:
        merged: list[list[int]] = []
        for start, end in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return [(start, end) for start, end in merged]

    def _collect_spans(
        self, entry: dict, day_spans: dict[str, list[tuple[int, int, bool]]], closed_days: set[str]
    ) -> None:
        for span in entry.get("openingHour") or []:
            if not isinstance(span, dict):
                continue
            day = sanitise_day(span.get("dayFrom"))
            if not day:
                self._count("hours/unknown_day")
                continue
            days = [day]
            last = sanitise_day(span.get("dayTo"))
            if last and last != day:
                # Multi-day span (Monday - Friday): expand the range,
                # wrapping past Sunday when the range wraps the weekend.
                order = self.WEEK_ORDER
                if order.index(last) > order.index(day):
                    days = order[order.index(day) : order.index(last) + 1]
                else:
                    days = order[order.index(day) :] + order[: order.index(last) + 1]
            if entry.get("isClosed"):
                # Closed marks cover the whole stated range, not just its
                # first day.
                closed_days.update(days)
                continue
            start = self._to_minutes(span.get("from"))
            end = self._to_minutes(span.get("to"))
            if start is None or end is None:
                self._count("hours/bad_range")
                continue
            # Overnight ranges pass through unmerged; OpeningHours splits
            # them at midnight when rendering.
            overnight = end <= start
            for one in days:
                day_spans.setdefault(one, []).append((start, end, overnight))

    def _hours_collect(self, channel: dict) -> tuple[dict[str, list[tuple[int, int, bool]]], set[str], bool]:
        # Buffer spans per weekday, skipping phone-only sets, dated rules
        # and exceptional types; availability flags ride along.
        day_spans: dict[str, list[tuple[int, int, bool]]] = {}
        closed_days: set[str] = set()
        always_open = False
        for entry in channel.get("serviceHours") or []:
            if not isinstance(entry, dict):
                continue
            if entry.get("serviceHourType") not in ("DaysOfTheWeek", "OverMidnight"):
                # Non-timetable types (single-date exceptions et al) are
                # deviations, not timetables.
                self._count("hours/skipped_type/" + str(entry.get("serviceHourType") or "missing"))
                continue
            if entry.get("validFrom") or entry.get("validTo"):
                self._count("hours/dated")
                continue
            if self._entry_is_phone(entry):
                # Phone availability ("puhelinaika") is not visit hours.
                self._count("hours/phone_only")
                continue
            if entry.get("isAlwaysOpen"):
                always_open = True
                continue
            self._collect_spans(entry, day_spans, closed_days)
        return day_spans, closed_days, always_open

    def _hours_render(
        self,
        oh: OpeningHours,
        day_spans: dict[str, list[tuple[int, int, bool]]],
        closed_days: set[str],
        always_open: bool,
        category: Categories | None,
    ) -> OpeningHours | str | None:
        # Availability records never override real timetables; lone
        # always-open renders 24/7 except for care/school kinds; per-day
        # spans merge overlaps and render once.
        if always_open and day_spans:
            # Availability records (on-call duty, shift care) never
            # override real timetables with 24/7 ("Uudenmaan aluetoimisto"
            # keeps Tu-Th 09:00-15:00).
            self._count("hours/always_open_with_spans")
        if always_open and not day_spans:
            if category in (
                Categories.SOCIAL_FACILITY,
                Categories.ASSISTED_LIVING,
                Categories.SCHOOL,
                Categories.COLLEGE,
                Categories.KINDERGARTEN,
                Categories.NURSING_HOME,
            ):
                # Staffed-around-the-clock care homes and schools are not
                # publicly walk-in 24/7; a 24/7 tag would mislead.
                self._count("hours/skipped_always_open_social")
                return None
            # Around-the-clock opening renders as a plain 24/7 string
            # (cf. other spiders), never overlapping spans.
            return "24/7"
        for day in self.WEEK_ORDER:
            spans = day_spans.pop(day, [])
            for start, end, overnight in spans:
                if overnight:
                    oh.add_range(
                        day,
                        f"{start // 60:02d}:{start % 60:02d}",
                        f"{end // 60:02d}:{end % 60:02d}",
                        time_format="%H:%M",
                    )
            plain = [(start, end) for start, end, overnight in spans if not overnight]
            if len(plain) > 1:
                merged = self._merge_spans([[start, end] for start, end in plain])
                if len(merged) < len(plain):
                    self._count("hours/merged")
                plain = merged
            for start, end in plain:
                oh.add_range(
                    day,
                    f"{start // 60:02d}:{start % 60:02d}",
                    f"{end // 60:02d}:{end % 60:02d}",
                    time_format="%H:%M",
                )
            if not spans and day in closed_days:
                oh.set_closed(day)
        return oh if oh.day_hours else None

    def _hours(self, channel: dict, category: Categories | None = None) -> OpeningHours | str | None:
        # Staff timetables arrive per service desk (nurse, counsellor,
        # psychologist, phone): buffer spans per weekday, drop phone-only
        # sets, union-merge overlaps, then render once. Deterministic
        # regardless of entry order (closed marks lose to real spans).
        oh = OpeningHours()
        day_spans, closed_days, always_open = self._hours_collect(channel)
        return self._hours_render(oh, day_spans, closed_days, always_open, category)

    SUBUNIT_RE = re.compile(r"(osasto|yksikkö|vastaanotto|klinikka|sosiaalityö|säilytys)")

    @staticmethod
    def _first_hit(resolvers: Iterable[Callable[..., SplitTriple | None]], *args) -> SplitTriple | None:
        # First non-None hit across an ordered precedence table. All
        # dispatch tables below share this shape; the table order IS the
        # precedence, each entry's comment the rationale.
        for resolver in resolvers:
            if (hit := resolver(*args)) is not None:
                return hit
        return None

    def _custom_category(self, name_fi: str) -> tuple | None:
        # Pre-table rules: unambiguous machines, shore/market guards and
        # scoped overrides the keyword table cannot express. Ordered
        # precedence table: first non-None hit wins, in this order.
        lowered = name_fi.lower()
        return self._first_hit(
            (
                self._custom_machine,
                self._custom_tori,
                self._custom_shore,
                self._custom_health,
                self._custom_church,
                self._custom_ward,
                self._custom_group_use,
                self._custom_exercise_ground,
            ),
            name_fi,
            lowered,
        )

    def _custom_machine(self, name_fi: str, lowered: str) -> tuple | None:
        if "keittiö" in lowered and "," in name_fi:
            # Comma-hosted kitchens survived the institutional-kitchen drop:
            # they are canteen units (Päiväkotikeittiö, Päiväkoti Pihapirtti).
            return Categories.CANTEEN, None
        if "lippuautomaatti" in lowered:
            # Ticket machines are unambiguous whatever square or museum
            # the name mentions; payment notes ride along (cf. service-map
            # machine names keeping korttimaksu/kolikkomaksu).
            extra: dict[str, str] = {"vending": "parking_tickets"}
            if "korttimaksu" in lowered:
                extra["payment:credit_cards"] = "yes"
                extra["payment:debit_cards"] = "yes"
            if "kolikkomaksu" in lowered:
                extra["payment:coins"] = "yes"
            return Categories.VENDING_MACHINE, extra
        return None

    # Facility and institution keywords outrank shore words: a named rink,
    # court, hall, school, clinic, office or care unit at a shore files
    # as itself, never the water ("Lauttasaaren uimaranta /
    # Beachvolleykenttä", "Päiväkoti Ankkalampi Duckies,
    # Herttoniemenranta").
    SHORE_FACILITY_BAIL = tuple(
        "kenttä volley pallo kaukalo luistelu sali halli koulu lukio opisto päiväkoti kirjasto museo kirkko "
        "kappeli sairaala neuvola terveysasema vastaanotto eläinlääkäri toimisto virasto poliisi apteekki "
        "teatteri terapia lataus kotihoito hoiva lyhytaikais asumispalvelu huoltorakennus rakennus leikki "
        "kalastus koirauimaranta ulkokuntoilu kuntoilupiste ".split()
    )

    def _custom_saari(self, lowered: str) -> tuple | None:
        # Islands proper ("Mustasaari", "Malkasaari (saari)"); venues
        # merely ON islands keep their filing (or generic) instead of
        # stealing the island tag. Compound-final only, like the shore nouns.
        # Runs AFTER the keyword table so real categories always win.
        if not re.search(r"\([A-ZÅÄÖa-zåäö-]*?(saari|luoto)\)", lowered) and not re.search(
            r"\w*(saari|luoto)$", lowered
        ):
            return None
        if "," in lowered:
            # Venue+place shapes ("Skopiayksikkö, Pietarsaari",
            # "Leivontakerho, Kyläsaari"): the island is the address.
            return None
        if any(
            word in lowered
            for word in (*self.SHORE_FACILITY_BAIL, "laituri", "yksikkö", "kauppa", "kerho", "ryhmä", "keskus")
        ):
            # Venue nouns in the name ("Korkeasaaren kauppa",
            # "Osaamiskeskus"): the venue is the POI, not the island.
            return None
        return None, {"place": "island"}

    def _custom_shore(self, name_fi: str, lowered: str) -> tuple | None:
        if self.SAUNA_RE.search(lowered):
            return Categories.SAUNA, None
        if "veneranta" in lowered:
            # Municipal boat shores ("Loppijärvi, Kuljun veneranta")
            # moor leisure craft: marinas, not beaches. Named facilities
            # at the shore still file as themselves.
            if any(word in lowered for word in (*self.SHORE_FACILITY_BAIL, "laituri")):
                return None
            return Categories.MARINA, None
        if (
            re.search(r"(?:\bsatama\b|\w+satama\b|\bsatamat\b|\w+satamat\b|\bsataman\b|\w+sataman\b)", lowered)
            and not ("kalasatama" in lowered and "vene" not in lowered)
            and "kotisatama" not in lowered
        ):
            # Kalasatama is a district and Kotisatama a proper name, not
            # harbours; combined boat-and-fishing harbours (vene- ja
            # kalasatama) moor leisure craft. Satamapuisto files under
            # puisto via the table. Parking, hospitality and facility
            # venues at harbours file as themselves, not the water.
            if re.search(r"(pysäköinti|parkki|kahvila|ravintola|kioski|kauppa)", lowered):
                return None
            if any(word in lowered for word in self.SHORE_FACILITY_BAIL):
                return None
            return Categories.MARINA, None
        if re.search(r"(?:\branta\b|\w+ranta\b)", lowered):
            # Shore compounds (Kirkkojärvenranta) and standalone shores
            # (Hotelli-ravintolan ranta); Rantala/Rantatie never match.
            # Parking, hospitality and facility venues named after shores
            # ("Pysäköintialue Asemanranta") file as themselves.
            if "talviuimaranta" in lowered:
                # Managed winter-swimming shores fall through to the table
                # instead of filing as beaches here.
                return None
            if re.search(r"(pysäköinti|parkki|kahvila|ravintola|kioski|kauppa)", lowered):
                return None
            if any(word in lowered for word in self.SHORE_FACILITY_BAIL):
                return None
            return Categories.NATURAL_BEACH, None
        if re.search(r"\bpaja\b", lowered):
            # Standalone workshops only (Janakkalan paja); Pajala stays whole.
            return Categories.SOCIAL_FACILITY, None
        if re.search(r"\bkota\b|\w+kota$", lowered) and "dakota" not in lowered:
            # Hut shelters, standalone (Utasen kota) or compound-final
            # (Vareskota); Kotikaari and Dakota stay whole.
            return Categories.SHELTER, None
        return None

    def _custom_tori(self, name_fi: str, lowered: str) -> tuple | None:
        # Market squares, with guards for lookalike compounds. Returns
        # None to fall through to the table (parking), (None, extra) for
        # placement-only squares, or a category.
        if not self.TORI_RE.search(lowered) or re.search(
            r"(lähitori|konttori|kuraattori|koordinaattori|kirpputori|navigaattori|palvelutori"
            r"|traktori|pastori|kanttori|reaktori|aattori)",
            lowered,
        ):
            # Lähitori (senior centres), konttori (offices), kuraattori
            # (counsellors), koordinaattori (coordinator desks), kirpputori
            # (flea markets), Navigaattori and Palvelutori (service desks)
            # end in tori without being squares, as do tractors, pastors,
            # cantors, reactors and -aattori coinages (Väriaattori artworks).
            return None
        if re.search(r"(pysäköinti|parkki)", lowered):
            # Parking at a square is parking, not the square.
            return None
        if any(
            word in lowered
            for word in (
                *self.SHORE_FACILITY_BAIL,
                "kaupungintalo",
                "neuvonta",
                "piste",
                "keskus",
                "palvelu",
                "shakki",
                "työllisyys",
                "tapahtuma",
            )
        ):
            # Named venues at squares file as themselves ("Kotkan 5.
            # Karhulan Tori apteekki", "Päiväkoti Vihtori", "Tiernan
            # koulu, Heinätori"): the square is the address, not the POI.
            return None
        if re.search(r"(kauppa|halli)", lowered):
            # Market halls and kauppa-squares trade; bare squares
            # (Töölöntori, Senaatintori) are places, not markets.
            return Categories.MARKETPLACE, None
        return None, {"place": "square"}

    def _custom_health(self, name_fi: str, lowered: str) -> tuple | None:
        if "päivystys" in lowered and re.search(r"(sosiaali|kriisi|poliisi)", lowered):
            # Non-medical on-call desks are not urgent-care clinics.
            if "poliisi" in lowered:
                return Categories.POLICE, None
            return Categories.SOCIAL_FACILITY, None
        if (
            any(word in lowered for word in self.SERVICE_HEADS)
            or "rokotus" in lowered
            or "hoitajan vastaanotto" in lowered
        ):
            # Hosted student-welfare and vaccination services file as
            # nurse-led clinics whatever the host (school, daycare):
            # the service outranks päiväkoti/koulu table rows.
            return Categories.CLINIC, {"healthcare": "nurse"}
        if re.search(r"\b(TYKS|OYS|HUS|TAYS|KYS)\b", name_fi, flags=re.IGNORECASE) and any(
            word in lowered for word in self.ACRONYM_UNIT_WORDS
        ):
            # Hospital-anchored units ("Vatsakeskus, Tays Hatanpää") are
            # departments, never generic or host-filed.
            return Categories.CLINIC, None
        if "neuvola" in lowered and re.search(r"(seniori|ikäihmis|vanhus)", lowered):
            # Senior clinics are clinics, not maternal care.
            return Categories.CLINIC, None
        if "neuvola" in lowered and re.search(r"(muisti|dement)", lowered):
            # Memory clinics (muistineuvola) are clinics, not maternal care.
            return Categories.CLINIC, None
        if re.search(r"(talousneuvola|velkaneuvonta)", lowered):
            # Financial advice desks are offices, not clinics.
            return Categories.OFFICE_GOVERNMENT, None
        if re.search(r"\w*lastensuojelu$", lowered):
            # Bare child-welfare service labels are offices, not facilities.
            return Categories.OFFICE_GOVERNMENT, None
        if "uimahalli" in lowered and "liikuntasali" in lowered:
            # Gym halls of swim centres ("Itäkeskuksen uimahalli /
            # Liikuntasali", cf. the uimahallin genitive table rule).
            return Categories.GYM, None
        return None

    def _custom_church(self, name_fi: str, lowered: str) -> tuple | None:
        if re.search(r"(kirkko|kappeli)$", lowered) and not re.search(
            r"(ortodoks|katol|helluntai|vapaakirkko|advent|baptist|metodist|mormoni|jehov|anglikaan)", lowered
        ):
            # Finnish parish churches are Evangelical Lutheran unless signed otherwise.
            return Categories.PLACE_OF_WORSHIP, {"religion": "christian", "denomination": "lutheran"}
        return None

    def _custom_ward(self, name_fi: str, lowered: str) -> tuple | None:
        if re.search(
            r"(lasten\s+ja\s+nuorten|nuorten)\s+.*\b(päiväsairaala|poliklinikka|terapiapoliklinikka|osasto|arviointiosasto|vastaanotto|fysioterapia|toimintaterapia|puheterapia|päivystys)\b",
            lowered,
        ):
            # Youth/pediatric clinical units ("Lasten ja nuorten
            # päiväsairaala", "Nuorten vastaanotto") are clinics, not
            # youth centres (outranking the nuorten community rule).
            if "päivystys" in lowered:
                return Categories.CLINIC_URGENT, None
            if "fysioterapia" in lowered:
                return Categories.CLINIC, {"healthcare": "physiotherapist"}
            if "puheterapia" in lowered:
                return Categories.CLINIC, {"healthcare": "speech_therapist"}
            return Categories.CLINIC, None
        if (
            re.search(
                r"\b(nuorisotyön|nuorisopalvelu\w*|nuorten)\b.*\b(toimisto|toimipiste|palvelupiste|asiakaspalvelu|ohjauspiste|neuvonta)",
                lowered,
            )
            or re.search(r"\bnuoriso-?\s*(?:ja\s+)?(?:liikunta)?toimisto\b", lowered)
        ) and not re.search(
            r"(psykiatr|poliklinikka|terapia|sairaala|klinikka|mielenterveys|päihde|nuorisotila|nuorisotalo|nuokkari|ungdomslokal|ungdomsgård)",
            lowered,
        ):
            # Youth administrative offices and guidance desks
            # ("Nuorisotoimisto", "Nuorisopalvelujen asiakaspalvelu",
            # "Nuoriso- ja liikuntatoimisto") are government offices,
            # not youth clubs; psychiatric clinics and youth rooms keep
            # their earlier table filings.
            return Categories.OFFICE_GOVERNMENT, None
        if re.search(r"(?:^|[\s-])osasto(?=\s|$)", lowered):
            # Bare wards/departments ("Malmin osasto 13", "Keuhko-osasto"):
            # hospital departments, not hospitals. Separator-anchored so
            # Kaupunginosa and Viestintäosasto never match.
            return Categories.CLINIC, None
        return None

    # Group nouns describing activities. Performing troupes (orkesteri)
    # are venues, never activities: orchestras file via their services.
    GROUP_NOUNS = ("ryhmä", "kerho", "kuoro", "joukkue", "parlamentti")
    # Group-noun compounds where the group IS the institution: the
    # facility prefix files via the table, never generic ("Päiväkotiryhmä
    # Vekkula" is the daycare; "Iltapäiväkerho" is the after-school club).
    # Pupil words (koululainen), education words (koulutus) and street
    # words (koulutie) never count as the school.
    GROUP_FACILITY_PREFIX = ("päiväkoti", "esiopetus", "koulu", "iltapäivä")
    GROUP_FACILITY_RE = re.compile(r"(päiväkoti|esiopetus|koulu|iltapäivä)(?!tie|katu|kuja|polku|väylä|lai|tus|ikä)")
    # Desk nouns elsewhere in a group name file the desk ("Vauvaperheryhmä
    # Untuva toimipiste" is the office); bare group numbers leave the venue
    # filing alone ("Kuntosali, ryhmä 1" stays the gym).
    GROUP_DESK_AMBIENT = ("toimipiste", "toimipaikka", "kuntosali")

    def _is_group_activity(self, lowered: str) -> bool:
        # Group-noun names describing an activity, never the venue: compound
        # group tokens (teatteriryhmä, ystäväryhmä, ulkokerho) and bare group
        # nouns with no facility filing. Peer-support groups (vertaisryhmä,
        # vertaistukiryhmä), senior clubs (seniorikerho), heart clubs
        # (sydänkerho), housing groups (asumis) and 4H clubs are venues and
        # never group activities. Mirrors _custom_group_use: rescue-tier only
        # calls this when the name tier left the row generic.
        for token in lowered.split():
            clean = token.strip(",.;:")
            m = re.search(r"[\w-]+(" + "|".join(self.GROUP_NOUNS) + r")$", clean)
            if not m:
                continue
            if clean.endswith(("leikkikerho", "leikkikoulu")):
                # Playgroup compounds ("Urheiluleikkikerho Kanervat") are
                # kindergartens via the table, never activities.
                continue
            if any(word in clean for word in ("vertais", "seniori", "sydän", "asumis", "4h-kerho")):
                continue
            if clean.startswith("pien"):
                # Size qualifiers ("pienryhmä") carry no venue info: the
                # activity/institution filing stands ("Kuparivuoren aamu- ja
                # iltapäivätoiminta ... pienryhmä" stays the after-school club).
                continue
            prefix = clean[: m.start(1)]
            if not prefix:
                # Bare group numbers ("Kuntosali, ryhmä 1") leave the venue
                # filing alone: not activities.
                continue
            if self.GROUP_FACILITY_RE.search(prefix):
                # The group is the institution: the table files it.
                continue
            return True
        return False

    def _custom_group_use(self, name_fi: str, lowered: str) -> tuple | None:
        # Inessive host nouns ("Kuusankosken kirjastossa") and group-noun
        # compounds (teatteriryhmä, kirjastoparlamentti) describe a service
        # or activity, never the venue: fall through to generic. Peer-support
        # groups (vertaisryhmä, vertaistukiryhmä) and senior clubs
        # (seniorikerho) are venues and file via the keyword table instead. Bare group numbers ("Kuntosali, ryhmä 1") leave the
        # venue filing alone; health contexts keep theirs.
        host_stems = self.INESSIVE_HOST_STEMS
        host_end = r"(?:ssa|ssä|lla|llä)$"
        if any(re.search(rf"{stem}{host_end}", token) for token in lowered.split() for stem in host_stems):
            # Hosted typed facilities ("Rintasyöpäseulonta ... sairaalassa")
            # file as themselves; untyped hosts stay generic.
            remainder = " ".join(
                token
                for token in lowered.split()
                if not any(re.search(rf"{stem}{host_end}", token) for stem in host_stems)
            )
            if self._has_fixture(remainder) or self._category(remainder)[0] is not None:
                return None
            return None, None
        if self._is_group_activity(lowered):
            remainder = " ".join(
                token.strip(",.;:")
                for token in lowered.split()
                if not re.search(r"[\w-]+(" + "|".join(self.GROUP_NOUNS) + r")$", token.strip(",.;:"))
            )
            if any(word in remainder for word in self.GROUP_DESK_AMBIENT):
                # Desk nouns outside the group token file the desk
                # ("Vauvaperheryhmä Untuva toimipiste" is the office;
                # "Kuntosali, ryhmä 1" stays the gym).
                return None
            if any(stem in remainder for stem in self.GROUP_FACILITY_PREFIX):
                # Institution nouns file the institution only when they head
                # it: before the group token ("Kämmenniemen päiväkoti
                # Terälahden lisäryhmä" is the daycare). Host schools after
                # the token ("...-ryhmä Lamminrahkan koulu -palvelun
                # järjestämispaikka", "...-ryhmä, Veittijärven koulu ...")
                # and paren addresses ("(Moision koulutie 2)") never type.
                first_group = re.search(r"[\w-]+(" + "|".join(self.GROUP_NOUNS) + r")", lowered)
                before = lowered[: first_group.start()] if first_group else ""
                if self.GROUP_FACILITY_RE.search(before):
                    return None
            if not re.search(
                r"(psykiatri|terapia|terveys|hoito|huolto|klinikka|sairaala|lääkäri|neuvola|mieli|päihde|vamma|hoiva|kuntout|rokot|hammas)",
                lowered,
            ):
                # Activity groups with no health context stay generic; health
                # contexts keep their table filing.
                return None, None
            return None
        if any(word in lowered for word in self.GROUP_DESK_AMBIENT):
            # Desk nouns in a group name file the desk; facility-prefixed
            # groups already fell through via _is_group_activity.
            return None
        return None

    def _custom_exercise_ground(self, name_fi: str, lowered: str) -> tuple | None:
        # Neighbourhood exercise grounds mirror the service-map activity
        # refinement: ball-game arenas are pitches, schoolyards read as
        # playgrounds (cf. Kungsgårdsskolan). Genitive grounds
        # ("...lähiliikuntapaikan miniareena", kk→k gradation) resolve like
        # nominative ones so specifics are not shadowed by the generic
        # fitness/table rows below.
        if "lähiliikuntapaikka" not in lowered and "lähiliikuntapaikan" not in lowered:
            return None
        if re.search(r"(miniareena|ministadion|pallopel|pallokentt|pelikentt|monitoimikentt)\w*", lowered):
            return Categories.LEISURE_PITCH, None
        if re.search(r"tenniskentt\w*", lowered):
            # Tennis courts read as pitches with the sport tagged (mirror
            # the table rule); tennis halls keep their hall filing below.
            return Categories.LEISURE_PITCH, {"sport": "tennis"}
        if re.search(r"tekonurmi\w*|tekokentt\w*", lowered):
            return Categories.LEISURE_PITCH, {"sport": "soccer", "surface": "artificial_turf"}
        if re.search(r"(koulu|skol|päiväkoti|päiväkodi)\w*", lowered):
            # Daycare yards read like schoolyards (playgrounds); the
            # gradation stem (päiväkodin) never contains the nominative.
            return Categories.LEISURE_PLAYGROUND, None
        return None

    def _carve_room_tail(self, name_fi: str) -> tuple[Categories | None, dict | None] | None:
        # Facility tails name the POI ("Hietarannan uimaranta /
        # Koripallokenttä"): the tail types it, not the host. Only clean
        # room-word tails with a real type carve; compound tails ("...
        # ja ...") and typeless tails keep full-form filing, while utility
        # buildings (huoltorakennus) stay deliberately generic.
        if " / " not in name_fi:
            return None
        tail = name_fi.rsplit(" / ", 1)[1].strip()
        if not tail:
            return None
        lowered = tail.lower()
        if "huoltorakennus" in lowered:
            # Utility-building tails never pose as the POI: the venue head
            # names and types it ("Väinämöisenkenttä / Huoltorakennus" is
            # the field). Untyped heads stay generic.
            self._count("category/room_building_venue")
            head = name_fi.rsplit(" / ", 1)[0].strip()
            category, extra = self._category(head)
            if category is None and extra is None:
                self._count("category/room_building_generic")
                return None, None
            return category, extra
        if not any(word in lowered for word in self.ROOM_WORDS):
            return None
        if self._is_institution(lowered.split(",")[0].strip()):
            # Institution tails are venues hosting an activity
            # ("Iltapäivätoiminta / Puotilan ala-aste, ..."), not rooms:
            # full-form filing stands (org tails ignored for the test).
            return None
        if re.search(r"\bja\b|&", lowered):
            return None
        category, extra = self._category(tail)
        if category is None:
            return None
        return category, extra

    def _carve_fused_room(self, name_fi: str) -> tuple[Categories | None, dict | None] | None:
        # Daycare-hosted rooms ("Hämeenkylän päiväkodin liikuntasali"):
        # the split names the unit with the daycare located, so the room
        # types the POI. School hosts already file via the table (sali
        # keys beat koulu) and never enter here; only the päiväkoti
        # shadow (which outranks every facility key) needs the carve.
        m = re.search(r"päiväkodin\s+(\S.*)$", name_fi.lower())
        if not m:
            return None
        tail = m.group(1).strip()
        if not tail or re.search(r"\bja\b|&", tail):
            return None
        if not any(word in tail for word in self.ROOM_WORDS):
            return None
        category, extra = self._category(tail)
        if category is None:
            return None
        self._count("category/fused_room_carve")
        return category, extra

    @staticmethod
    def _strip_ostopalvelu(text: str) -> str:
        # Purchased-service qualifiers ("..., Hämeenlinna, yhteisöllisen
        # asumisen ostopalvelut", "... ostopalveluna") arrange the service,
        # never the place or venue.
        stripped = re.sub(r",\s*[^,]*(?:ostopalvelu\w*)\s*$", "", text).strip()
        return re.sub(r"\s+ostopalveluna\s*$", "", stripped, flags=re.IGNORECASE).strip()

    def _category(self, name_fi: str) -> tuple[Categories | None, dict | None]:
        # Invisible characters (zero-width, soft hyphens) never carry
        # matching meaning; strip them so feed dirt can't hide keywords.
        # Purchased-service tails strip so desks behind care-home heads
        # stay homes.
        name_fi = self._strip_ostopalvelu(self._visible(name_fi))
        if (custom := self._custom_category(name_fi)) is not None:
            return custom
        if (carved := self._carve_room_tail(name_fi)) is not None:
            return carved
        if (fused := self._carve_fused_room(name_fi)) is not None:
            return fused
        lowered = name_fi.lower()
        # Gradation plurals/genitives never contain their singular
        # (kenttä/kentät/kentän, ranta/rannat/rannan, keskus/keskuksen,
        # seulonta/seulonnat/seulonnan, päiväkoti/päiväkodit/päiväkotien,
        # paikka/paikat/paikkojen/paikan): normalize the known stems first.
        lowered = self.GRADATION_RE.sub(lambda m: self.GRADATION_MAP[m.group(0)], lowered)
        for rx, category, extra in self._rules:
            if rx.search(lowered):
                if category == Categories.HOSPITAL and self.SUBUNIT_RE.search(lowered):
                    # Wards, units and receptions are hospital departments,
                    # not hospitals (cf. service-map ward refinement).
                    if "päivystys" in lowered:
                        return Categories.CLINIC_URGENT, None
                    return Categories.CLINIC, None
                return category, extra
        if (island := self._custom_saari(lowered)) is not None:
            # Genuine islands file only when no keyword typed the row.
            return island
        if "koti" in lowered:
            # Home-named places without a sharper filing (islands handled
            # above) are group/housing homes.
            return Categories.SOCIAL_FACILITY, None
        return None, None

    def _normalize_phone(self, raw: str) -> str | None:
        # National trunk (09..., 020..., 0295...) folds to +358 form;
        # a stray 0 after +358 drops; a duplicated country code repairs;
        # anything else (short codes like 116 006, foreign numbers,
        # invalid lengths) passes through untouched or drops.
        digits = re.sub(r"\D", "", raw)
        if not digits:
            # Non-numeric junk ("null", "no phone") is never a phone number.
            self._count("contact/phone_not_numeric")
            return None
        if raw.strip().startswith("+"):
            if digits.startswith("359") and len(digits) == 12:
                # Single-digit country typo on a Finnish number
                # ("+359 447301262" in Ikaalinen): repair to +358.
                self._count("contact/country_typo")
                digits = "358" + digits[3:]
            if not digits.startswith("358"):
                return raw.strip() or None
            digits = digits[3:].lstrip("0")
            if digits.startswith("358") and len(digits) in (9, 10):
                # Doubled country code ("+358 358..."): strip and repair
                # the trunk like other trunk-less numbers.
                digits = digits[3:]
        else:
            if digits.startswith("358") and len(digits) in (9, 10):
                # Country code without "+" on a short number ("358912345"):
                # strip it, then repair the trunk like other trunk-less numbers.
                digits = "0" + digits[3:]
            if digits.startswith("358") and len(digits) in (11, 12):
                # Country code without "+" ("358 17499111").
                digits = digits[3:]
            elif not digits.startswith("0"):
                if len(digits) in (8, 9):
                    # Trunk lost in the feed ("400395234"): repair it.
                    digits = "0" + digits
                elif len(digits) == 10 and digits[0] in ("4", "5"):
                    # Trunk-less 10-digit strings ("4578757018") exceed the
                    # national format: drop, never reformat.
                    self._count("contact/phone_too_long")
                    return None
                else:
                    return raw.strip() or None
            digits = digits.lstrip("0")
        if not digits:
            # Non-numeric junk ("null") is never a phone number.
            self._count("contact/phone_empty")
            return None
        if digits.startswith("358") and len(digits) > 10:
            # Duplicated country code from a feed concat ("+358 358...").
            digits = digits[3:]
        if not (5 <= len(digits) <= 10):
            self._count("contact/phone_bad_length")
            return None
        if digits[0] in ("4", "5") and len(digits) == 9:
            # Mobile prefixes stay readable ("+358 50 9119693").
            return "+358 " + digits[:2] + " " + digits[2:]
        if len(digits) == 10:
            # Too long for the national format (trunk-less 10-digit strings
            # like "4578757018" are feed garbage): drop, never reformat.
            self._count("contact/phone_too_long")
            return None
        if len(digits) <= 7:
            # Short landlines split the single-digit area ("+358 9 4711").
            return "+358 " + digits[:1] + " " + digits[1:]
        return "+358 " + digits

    # Placeholder email locals: template text, never mailboxes.
    PLACEHOLDER_EMAILS = frozenset(
        "etunimi.sukunimi firstname.lastname nimi.sukunimi fornamn.efternamn förnamn.efternamn "
        "förnamn.släktnamn ".split()
    )

    @staticmethod
    def _str_or_empty(value: object) -> str:
        return value.strip() if isinstance(value, str) else ""

    @staticmethod
    def _canonical_phone_digits(raw: str) -> str:
        # Feed shapes vary (+358 prefix, 09 trunk, bare local): compare
        # the national-significant digits so all shapes hit the same set.
        digits = re.sub(r"\D", "", raw or "")
        if digits.startswith("358"):
            digits = digits[3:]
        if digits.startswith("0"):
            digits = digits[1:]
        return digits

    def _contact_phone(self, item: Feature, phones: list) -> None:
        # First voice line wins; fax lines, generic switchboards and
        # unusable entries fall through to the next candidate.
        for entry in phones:
            if not isinstance(entry, dict):
                continue
            if (entry.get("type") or "Phone").strip().lower() != "phone":
                # Fax and other non-voice lines never pose as the phone
                # ("Konsertti- ja kongressitalo Mikaeli" led with one).
                continue
            number = self._str_or_empty(entry.get("number"))
            prefix = self._str_or_empty(entry.get("prefixNumber"))
            if not number:
                continue
            if self._canonical_phone_digits(prefix + number) in self.GENERIC_PHONES:
                self._count("contact/generic_hotline")
                continue
            raw = f"{prefix} {number}".strip() if prefix else number
            if normalized := self._normalize_phone(raw):
                item["phone"] = normalized
                return

    def _contact_email(self, item: Feature, emails: list) -> None:
        # First usable mailbox wins; placeholders yield to real seconds.
        for entry in emails:
            if not isinstance(entry, dict):
                continue
            email = self._str_or_empty(entry.get("value"))
            if not email or "@" not in email:
                continue
            if email.lower() in self.GENERIC_EMAILS:
                self._count("contact/generic_email")
                continue
            if email.split("@")[0].lower() in self.PLACEHOLDER_EMAILS:
                self._count("contact/placeholder_email")
                continue
            item["email"] = email
            return

    def _contact_website(self, item: Feature, pages: list) -> None:
        # First usable page wins; login walls and mailto-shaped URLs fall
        # through to the institution's own site.
        for entry in pages:
            if not isinstance(entry, dict):
                continue
            url = self._str_or_empty(entry.get("url"))
            if not url:
                continue
            if self.LOGIN_URL_RE.search(url):
                self._count("contact/login_url")
                continue
            if "finlex.fi" in url.lower():
                # Legislation references are never the venue website.
                self._count("contact/law_reference")
                continue
            item["website"] = url
            return

    def _apply_contact(self, item: Feature, channel: dict) -> None:
        phones = channel.get("phoneNumbers") or []
        if isinstance(phones, list):
            self._contact_phone(item, phones)
        emails = channel.get("emails") or []
        if isinstance(emails, list):
            self._contact_email(item, emails)
        pages = channel.get("webPages") or []
        if isinstance(pages, list):
            self._contact_website(item, pages)

    # Housenumber with optional letter and range ("Katutie 2a" stays whole,
    # "Nummentie 12 - 14" folds to "12-14"). PTV-local copy of the
    # service-map token rules; the driver differs (split street/number
    # fields, comma/slash tails inside the number field).
    HOUSENUMBER_RE = re.compile(r"\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?")
    # Staircase/room/door tails after a housenumber, in priority order:
    # (min tokens, housenumber offset, middle, last, join). Mid patterns
    # compiled without flags (the (?i:as) entry carries its own inline
    # flag, as before); last patterns compiled with their flags.
    STAIRCASE_RULES = (
        (4, 3, re.compile(r"\d+[A-Za-z]?"), re.compile(r"[A-Za-z]{1,2}"), "MID LAST"),
        (4, 3, re.compile(r"[A-Za-z]"), re.compile(r"\d+(?:-\d+)?[A-Za-z]?"), "MID LAST"),
        (4, 3, re.compile(r"[A-Za-z]"), re.compile(r"[A-Za-z]"), "MID-LAST"),
        (4, 3, re.compile(r"(?i:as)"), re.compile(r"\d+[A-Za-z]?", re.IGNORECASE), "MID LAST"),
        (3, 2, None, re.compile(r"[A-Za-z]{1,2}(?:-[A-Za-z]{1,2})?|\d+"), "LAST"),
        (
            3,
            2,
            None,
            re.compile(r"[A-Za-z]{1,2}\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?|[A-Za-z]-(?:ovi|rappu)", re.IGNORECASE),
            "LAST",
        ),
    )
    # Tails describing everything but the street address. Finnish floor
    # text strips from the address string; the number is kept separately
    # as addr:floor, never OSM level.
    ADDR_STRIP_RULES = (
        re.compile(r"\s*\([^)]*\)"),
        re.compile(r",\s*[\d\s&\.,-]*(krs|kerros|vån|våning|rak\.?|rakennus)\b.*$"),
        re.compile(r"\s+\d+\.?\s*(krs|kerros|vån|våning)\b.*$"),
        re.compile(r"/\s*\d+\.?\s*(krs|kerros|vån|våning)\b.*$"),
        re.compile(r"\s+(rak\.?|rakennus|krs|kerros|vån|våning)\b.*$"),
        re.compile(r"\s+-\s*(sisään\w*|käynti\w*|sisäpiha|porras|ovi|entrance)\b.*$", re.IGNORECASE),
        re.compile(r"\s+vastapäätä[\s.!]*$", re.IGNORECASE),
    )
    # PO-box tails inside the number field ("Kolpintie 7, PL 111").
    POBOX_TAIL_RE = re.compile(r"pl\b.*$", re.IGNORECASE)
    # Building tails kept as units ("Kunnallissairaalantie 20, rakennus 7").
    BUILDING_TAIL_RE = re.compile(r"(\b(rak\.?|rakennus)\b|\w*talo\b)\s*[\w.]*$", re.IGNORECASE)
    # Stair/door/apartment tails kept as units ("2, A-ovi"; "11, A").
    UNITWORD_TAIL_RE = re.compile(
        r"([A-Za-z]\s+)?(asunto|\bas\b|rappu|huoneisto|liikehuoneisto|porras|ovi)\b\s*[\w.]*$", re.IGNORECASE
    )
    # Door/room/apartment words inside the number field ("15 ovi 28",
    # "365 E as 5", "18 A Hki 53", "2 ja 4"): the first housenumber
    # counts, the rest is the unit.
    NUMBER_WORD_TAIL_RE = re.compile(r"(ovi|\bas\b|asunto|rappu|tsto|\bhki\b|huoneisto|\bja\b)", re.IGNORECASE)
    # Place suffixes for numberless addresses (squares, islands...), street
    # suffixes for bare streets. PTV-local copies of the service-map lists.
    PLACE_SUFFIXES = tuple(
        "saari luoto niemi lahti järvi lampi koski joki kanava salmi puisto tori aukio kenttä metsä niitty "
        "pelto vaara mäki kallio asema ö kari selkä laituri saaristo holme holmen viken sjö sjön parken "
        "torget skär ".split()
    )
    STREET_SUFFIXES = tuple(
        "tie katu kuja polku väylä raitti ranta kaari penger esplanadi bulevardi vägen väg gatan gata gränden "
        "gränd stigen stig väli linja kurvi ".split()
    )
    # Street-stem alternation shared by street-tail/paren regexes
    # (linja stays STREET_SUFFIXES-only so linja-autoasema never matches;
    # ranta stays out of numberless street checks because it doubles as
    # a shore/venue suffix).
    STREET_STEM_ALT = "|".join(s for s in STREET_SUFFIXES if s not in ("ranta", "linja"))
    STREET_NUMBERED_ALT = "|".join(s for s in STREET_SUFFIXES if s != "linja")
    COMMA_STREET_RE = re.compile(r"(" + STREET_NUMBERED_ALT + r")\s+\d")

    def _strip_addr_base(self, address: str) -> str:
        address = self._visible(address).replace("–", "-").replace("—", "-")
        base = address
        for rx in self.ADDR_STRIP_RULES:
            base = rx.sub("", base).strip()
        return base

    # Floor markers and ordinal stems for addr:floor extraction. A number
    # only counts with an adjacent marker: ordinal street names (Toinen
    # linja, Andra linjen) never match. Finnish kerros is 1-based, so the
    # value goes to addr:floor, never OSM level (0-based). Street-level
    # notes (katutaso, pohjakerros) stay dropped: their numbering is
    # ambiguous, and guessing it would invent data.
    FLOOR_MARKER = r"(?:krs\.?|kerro\w*|vån(?:ing(?:en)?)?\.?)"
    FLOOR_ORDINALS = (
        ("ensimmä", "1"),
        ("första", "1"),
        ("toinen", "2"),
        ("toise", "2"),
        ("andra", "2"),
        ("kolma", "3"),
        ("tredje", "3"),
        ("nelj", "4"),
        ("fjärde", "4"),
        ("viid", "5"),
        ("femte", "5"),
        ("kuud", "6"),
        ("sjätte", "6"),
        ("seitsem", "7"),
        ("sjunde", "7"),
        ("kahdeks", "8"),
        ("åttonde", "8"),
        ("yhdeks", "9"),
        ("nionde", "9"),
        ("kymmen", "10"),
        ("tionde", "10"),
    )

    def _extract_floor(self, *texts: str) -> str | None:
        # Exactly one marker-anchored floor number across the address
        # strings ("4, 3. krs", "7 A (3. kerros)", "4 a, toinen. krs",
        # "7 A (kolmannes kerros)"). Multi-floor lists ("5 (3. ja,
        # 4. krs)", "2, 5 ja 7. krs") stay ambiguous: None.
        marker = self.FLOOR_MARKER
        for text in texts:
            if re.search(
                r"\d+\s*\.?\s*,?\s*(?:ja|&|-|–|/)\s*[^a-zåäö]*?\d+\s*\.?\s*" + marker,
                text,
                flags=re.IGNORECASE,
            ):
                return None
        pattern = re.compile(
            r"(\d+)\s*\.?\s*" + marker + r"\b|([A-Za-zåäöÅÄÖ]+)\s*\.?\s*" + marker + r"\b",
            flags=re.IGNORECASE,
        )
        found = []
        for text in texts:
            for match in pattern.finditer(text):
                if match.group(1) is not None:
                    found.append(match.group(1))
                else:
                    word = match.group(2).lower()
                    for stem, number in self.FLOOR_ORDINALS:
                        if word.startswith(stem):
                            found.append(number)
                            break
        if len(set(found)) == 1:
            return found[0]
        return None

    def _split_addr_tokens(self, tokens: list[str]) -> tuple[str, str, str | None] | None:
        # Returns (street, housenumber, unit); PTV-local port of the
        # service-map token rules (spaced letters fold, staircases split).
        number = self.HOUSENUMBER_RE
        tokens = [clean for t in tokens if (clean := t.strip().strip(",.;"))]
        if len(tokens) >= 3 and re.fullmatch(r"\d+", tokens[-3]) and re.fullmatch(r"[a-zåäö]", tokens[-2]):
            tokens = tokens[:-3] + [tokens[-3] + tokens[-2]] + tokens[-1:]
        elif len(tokens) == 3 and re.fullmatch(r"\d+", tokens[-2]) and re.fullmatch(r"[a-zåäö]", tokens[-1]):
            tokens = tokens[:-2] + [tokens[-2] + tokens[-1]]
        if len(tokens) >= 2 and (dotted := re.fullmatch(r"(\d+)\.([A-Za-z]\.\d+)", tokens[-1])):
            return " ".join(tokens[:-1]), dotted.group(1), dotted.group(2)
        if (
            len(tokens) >= 4
            and re.fullmatch(number, tokens[-3])
            and tokens[-2] == "-"
            and re.fullmatch(number, tokens[-1])
        ):
            tokens = tokens[:-3] + [tokens[-3] + "-" + tokens[-1]]
        for min_len, offset, mid, last, join in self.STAIRCASE_RULES:
            if len(tokens) < min_len:
                continue
            if not re.fullmatch(number, tokens[-offset]):
                continue
            if mid is not None and not mid.fullmatch(tokens[-2]):
                continue
            if not last.fullmatch(tokens[-1]):
                continue
            if join == "MID LAST":
                unit = tokens[-2] + " " + tokens[-1]
            elif join == "MID-LAST":
                unit = tokens[-2] + "-" + tokens[-1]
            else:
                unit = tokens[-1]
            return " ".join(tokens[:-offset]), tokens[-offset], unit
        if len(tokens) >= 2 and re.fullmatch(number, tokens[-1]):
            return " ".join(tokens[:-1]), tokens[-1], None
        if len(tokens) >= 2 and (match := re.fullmatch(r"(\d+[A-Za-z]+)(\d+[A-Za-z]*)", tokens[-1])):
            return " ".join(tokens[:-1]), match.group(1), match.group(2)
        return None

    def _resolve_number_tail(self, tail: str) -> str | None:
        # Comma tails inside the number field resolve to units or dropped
        # descriptors; None drops.
        if re.search(r"(krs|kerros|vån|våning)\b", tail, flags=re.IGNORECASE):
            self._count("address/floor_tail")
            return None
        if re.match(r"\d{5}\b", tail):
            # Postcode leaked into the number field (sibling case in
            # _apply_address filters postcodes out of the unit slot).
            self._count("address/postcode_in_unit")
            return None
        if self.POBOX_TAIL_RE.search(tail):
            self._count("address/pobox_dropped")
            return None
        if (
            self.BUILDING_TAIL_RE.search(tail)
            or self.UNITWORD_TAIL_RE.search(tail)
            or re.fullmatch(r"[A-Za-z]{1,2}(?:-(?:ovi|rappu))?", tail, flags=re.IGNORECASE)
            or self._has_digit(tail)
        ):
            self._count("address/comma_unit")
            return tail
        self._count("address/descriptor_dropped")
        return None

    def _number_sanitize(self, number: str) -> str:
        # Straight-line field cleanups: postcode leaks, duplicated "ja"
        # numbers, lt artifacts, slash venues, unclosed parens and
        # space-form building tails. Pure string rewrites plus counters.
        stripped = re.sub(r"\s*\b\d{5}\b\s*\S.*$", "", number).strip()
        if stripped != number.strip():
            # Postcode tails leak into the number field ("3 03100 Nummela").
            self._count("address/postcode_in_number")
            number = stripped
        bare_tail = re.sub(r"\s+\b\d{5}\b\s*$", "", number).strip()
        if bare_tail != number.strip() and self._has_digit(bare_tail):
            # Bare postcode tails ("Tie 10 11111" with no postcode field):
            # postcodes are never housenumbers or units.
            self._count("address/postcode_in_number")
            number = bare_tail
        if re.fullmatch(r"\d{5}", number.strip()):
            # A lone postcode leaked into the number field ("90570" while
            # the real number sits inside the street line): no housenumber.
            self._count("address/postcode_only_number")
            number = ""
        doubled = re.sub(r"\b(\d+[A-Za-z]?)\s+ja\s+\1\b", r"\1", number).strip()
        if doubled != number.strip():
            # Duplicated housenumbers ("21 ja 21").
            self._count("address/dup_number")
            number = doubled
        lt_stripped = re.sub(r"^\d+\s+lt\s+", "", number, flags=re.IGNORECASE).strip()
        if lt_stripped != number.strip() and re.match(r"^\d", lt_stripped):
            # Feed artifact numbers ("1 lt 7"): the trailing number counts.
            self._count("address/lt_dropped")
            number = lt_stripped
        head, _, slash = number.partition("/")
        if slash.strip():
            if re.fullmatch(r"\d+[A-Za-z]?", head.strip()) and re.fullmatch(
                r"\d+[A-Za-z]?(?:\s*-\s*\d+[A-Za-z]?)?", slash.strip()
            ):
                # Dual housenumbers ("12/14", corner building): both halves
                # count, folded to the range form.
                self._count("address/dual_number")
                number = head.strip() + "-" + slash.strip()
            else:
                # Venue notes inside the number field ("/ Espoon Keskuspuisto").
                self._count("address/venue_tail_dropped")
        raw_head = number.partition("/")[0]
        unclosed = re.sub(r"\s*\([^()]*$", "", raw_head).strip()
        if unclosed != raw_head.strip():
            # A second, unterminated address in the number field
            # ("17a (Metsolantie 18, Peller..."): the first number counts.
            self._count("address/paren_tail_dropped")
            raw_head = unclosed
        head = re.sub(r"(?<!,)\s+((?:rak\.?|rakennus)\b)", r", \1", raw_head, flags=re.IGNORECASE).strip()
        if head != raw_head.strip():
            # Space-form building tails ("15 rak.1 B-rappu") resolve like
            # the comma form ("8, rak. N, B-rappu"): housenumber plus unit.
            self._count("address/building_tail")
        return head

    def _number_core_units(self, head: str) -> tuple[str, list[str]]:
        # Comma split, district tails, worded cores, premises descriptors,
        # zero/PO-box cores and unit tails.
        parts = [p.strip() for p in head.split(",") if p.strip()]
        core = parts[0] if parts else ""
        if core:
            district = re.match(r"^(\d+[A-Za-z]?(?:\s*-\s*\d+[A-Za-z]?)?)\s+([A-ZÅÄÖ][a-zåäö]{2,})$", core)
            if (
                district
                and not self.BUILDING_TAIL_RE.search(district.group(2))
                and not self.UNITWORD_TAIL_RE.search(district.group(2))
                and not re.fullmatch(r"[A-Za-z]{1,2}(?:-(?:ovi|rappu))?", district.group(2), flags=re.IGNORECASE)
                and self._has_no_digit(district.group(2))
            ):
                # District tails inside the number field ("1 Alppiharju"):
                # the housenumber counts, the district drops.
                self._count("address/district_tail_dropped")
                core = district.group(1)
                parts = [core, *parts[1:]]
        if core:
            worded = re.match(r"^(\d+[A-Za-z]?(?:\s*-\s*\d+[A-Za-z]?)?)\s+(.+)$", core.strip())
            if (
                worded
                and self._has_digit(worded.group(2))
                and "(" not in worded.group(2)
                and not re.search(r"(krs|kerros|vån|våning)\b", worded.group(2), flags=re.IGNORECASE)
                and (
                    self.NUMBER_WORD_TAIL_RE.search(worded.group(2)) or re.match(r"^[A-Za-z]\s+\S*\d", worded.group(2))
                )
            ):
                self._count("address/word_token")
                core = worded.group(1)
                parts = [core, re.sub(r"^\bja\b\s+", "", worded.group(2).strip()), *parts[1:]]
            premise = re.match(r"^(\d+[A-Za-z]?(?:\s*-\s*\d+[A-Za-z]?)?)\s+([A-Za-zåäö].*)$", core, flags=re.IGNORECASE)
            if premise and re.search(
                r"(liiketila|toimitila|toimistotila|toimisto|liikehuoneisto|huoneisto|asunto|asunnot|asunnon|varasto|autotalli)",
                premise.group(2),
                flags=re.IGNORECASE,
            ):
                # Premises descriptors inside the number field
                # ("4 Liiketila 3B-120"): housenumber plus unit.
                self._count("address/premise_unit")
                core = premise.group(1)
                parts = [core, premise.group(2).strip(), *parts[1:]]
        if core == "0":
            # Zero numbers mark numberless sites, never a housenumber.
            self._count("address/zero_number")
            core = ""
        elif core and self.POBOX_TAIL_RE.match(core):
            # A PO box as the whole number ("PL 24"): no housenumber.
            self._count("address/pobox_number")
            core = ""
        units = []
        for tail in parts[1:]:
            if (unit := self._resolve_number_tail(tail)) is not None:
                units.append(unit)
        return core, units

    def _number_parts(self, number: str) -> tuple[str, list[str]]:
        return self._number_core_units(self._number_sanitize(number))

    # Island infixes routing numberless sites to addr:place
    # ("Talholmen virkistysalue", whose tail is not a place suffix).
    ISLAND_INFIX = ("saari", "luoto", "holm", "skär")

    def _route_placeless(self, item: Feature, raw: str) -> None:
        # Numberless roads: single-token non-streets and named places go to
        # addr:place, bare streets and the rest stay on the line.
        lowered = raw.lower()
        if len(raw.split()) == 1 and not self._endswith_any(lowered, self.STREET_SUFFIXES):
            self._count("address/place")
            item["extras"]["addr:place"] = raw
            return
        if self._endswith_any(lowered, self.PLACE_SUFFIXES):
            if self._endswith_any(raw.split()[-1].lower(), ("asema", "selkä", "laituri")):
                # Stations, open water and piers are not addr:place values.
                self._count("address/place_station")
                item["addr_full"] = raw
            else:
                self._count("address/place")
                item["extras"]["addr:place"] = raw
            return
        if not self._endswith_any(lowered, self.STREET_SUFFIXES) and any(word in lowered for word in self.ISLAND_INFIX):
            # Island sites whose tail is a zone noun, not a place suffix
            # ("Talholmen virkistysalue").
            self._count("address/place_island")
            item["extras"]["addr:place"] = raw
            return
        is_street = self._endswith_any(lowered, self.STREET_SUFFIXES)
        self._count("address/bare_street" if is_street else "address/freeform")
        if is_street:
            item["street"] = raw
        else:
            item["addr_full"] = raw

    def _road_base(self, road: str) -> str:
        # Venue-prefixed roads ("Didrichsenin taidemuseo, Kuusilahdenkuja"):
        # keep the comma-part that reads as a street/place, drop the venue.
        # Generic tails ("Castreninkatu, puisto") keep the street head.
        if "," not in road:
            return road
        parts = [p.strip() for p in road.split(",") if p.strip()]
        if len(parts) < 2:
            return road
        scored = []
        for part in parts:
            lowered = part.lower()
            if self._endswith_any(lowered, self.STREET_SUFFIXES):
                scored.append(2)
            elif self._endswith_any(lowered, self.PLACE_SUFFIXES):
                scored.append(1)
            else:
                scored.append(0)
        if max(scored) == 0:
            return road
        # Tie between two scored parts: prefer the tail (venue-prefix
        # order puts the road last); a lone scored head still wins.
        top = [i for i, s in enumerate(scored) if s == max(scored)]
        best = top[-1]
        if parts[best] != road:
            self._count("address/road_venue_prefix")
        return parts[best]

    def _address_number_dup(self, road: str | None, number: str) -> str:
        # The road already ends with the number-field content
        # ("Kauppakuja 2 A 1" + "2 A 1"): never parse it twice.
        if road and number and road.strip().endswith(number.strip()):
            self._count("address/road_number_dup")
            return ""
        return number

    def _address_route(self, item: Feature, road: str | None) -> str | None:
        # Route descriptions ("Metsäautotie välillä Lapinlahdentie 1175
        # - Pitkämäentie 641", feed typo "välilla") are not postal
        # addresses: keep whole.
        if road and re.search(r"\bvälil(?:lä|la)\b", road, flags=re.IGNORECASE):
            self._count("address/route_desc")
            item["addr_full"] = self._strip_addr_base(road) or road
            return None
        return road

    def _address_wordled(self, core: str, units: list[str], road: str | None) -> tuple[str, list[str]]:
        # Word-led cores on already-numbered roads ("talo 7" on
        # "Tikkamäentie 16"): the road keeps its number, the core
        # is a unit tail.
        if core and not re.match(r"^\d", core) and self._has_digit(core) and re.search(r"\d[A-Za-z]?\s*$", road or ""):
            self._count("address/wordled_core_unit")
            return "", [core, *units]
        return core, units

    def _strip_road_city(self, road: str | None, number: str, city_src: str | None) -> tuple:
        # City tails repeat the structured municipality, never the road:
        # the city leaked into the number field ("Tahtimarssi 3" with
        # number "Oulu") or rides the road line ("Pappilantie 11,
        # pielavesi", "Mäntymäentie 55, 13700 hattula").
        if number and city_src and self._has_no_digit(number) and number.casefold() == city_src.strip().casefold():
            self._count("address/city_in_number")
            number = ""
        if road and "," in road and not number and city_src:
            head, _, tail = road.rpartition(",")
            tail = re.sub(r"^\d{5}\s+", "", tail.strip()).strip()
            if head.strip() and tail and tail.casefold() == city_src.strip().casefold():
                self._count("address/road_city_tail")
                road = head.strip()
        return road, number

    def _address_token_assign(self, item: Feature, raw: str, units: list[str], postcode: str | None) -> None:
        # Tokenize the road+core line into street/house/unit, dropping
        # duplicates and postcode leaks; unparseable lines stay whole.
        if raw and self._has_no_digit(raw):
            self._route_placeless(item, raw)
        elif parsed := self._split_addr_tokens(raw.split()):
            addr_street, house, unit = parsed
            fixed = house.lower()
            if fixed != house:
                self._count("address/letter_case")
                house = fixed
            item["street"] = addr_street
            item["housenumber"] = house
            if unit:
                self._count("address/stair_unit")
                units.append(unit)
            folded = re.search(r"[A-Za-z]+$", house)
            for dup in list(units):
                if dup == house or (folded and dup.casefold() == folded.group(0).casefold()):
                    # Unit duplicating the housenumber ("51" with house
                    # 51, or a staircase already folded in): not a unit.
                    self._count("address/dup_unit_dropped")
                    units.remove(dup)
            if postcode:
                # Postcode leaked into the unit slot ("67100" with house
                # 4): postcodes are never units (sibling case in
                # _resolve_number_tail drops them from comma tails).
                dropped = [u for u in units if u == postcode]
                if dropped:
                    self._count("address/postcode_in_unit", len(dropped))
                units = [u for u in units if u != postcode]
            if units:
                item["extras"]["addr:unit"] = " ".join(units)
        else:
            self._count("address/unparsed")
            item["addr_full"] = raw
            if units:
                item["extras"]["addr:unit"] = " ".join(units)

    def _apply_address(self, item: Feature, street: dict, postcode: str | None, city_src: str | None) -> None:
        road = self._lang_value(street.get("street") or [], "fi", "sv", "en")
        number = (street.get("streetNumber") or "").strip()
        if road and road[0].islower():
            # Feed roads starting lowercase ("wetterhoffinkatu").
            self._count("address/road_case")
            road = self._cap_first(road)
        if road and re.match(r"^(pl|p\.l\.)\b", road.strip(), flags=re.IGNORECASE):
            # PO boxes filed as streets ("PL 52"): no visit address, but
            # the channel keeps its city, postcode and coords.
            self._count("address/pobox_road")
            road, number = None, ""
        road, number = self._strip_road_city(road, number, city_src)
        number = self._address_number_dup(road, number)
        road = self._address_route(item, road)
        # Floors extract from the raw fields before any stripping: the
        # tails below drop the floor text ("7 A (3. kerros)"), while the
        # number survives as addr:floor. Reads the pre-road_base road so
        # a comma part carrying the floor is never missed.
        floor = self._extract_floor(number, road or "")
        if road and "," in road:
            road = self._road_base(road)
        if road and "/" in road:
            # Corner buildings name two streets; no single postal address.
            # The housenumber has no street to attach to, but unit tails
            # still parse via the shared token rules ("12 A 1" → "A 1").
            self._count("address/cross")
            core, units = self._number_parts(number)
            core, units = self._address_wordled(core, units, road)
            raw = self._strip_addr_base(f"{road} {core}".strip() if core else road)
            if raw and (tok := self._split_addr_tokens(raw.split())):
                if tok[2]:
                    self._count("address/stair_unit")
                    units.append(tok[2])
            item["addr_full"] = self._strip_addr_base(road) or road
            if units:
                item["extras"]["addr:unit"] = " ".join(units)
        elif road:
            core, units = self._number_parts(number)
            core, units = self._address_wordled(core, units, road)
            raw = self._strip_addr_base(f"{road} {core}".strip() if core else road)
            self._address_token_assign(item, raw, units, postcode)
        if floor is not None:
            self._count("address/floor")
            item["extras"]["addr:floor"] = floor
        item["postcode"] = postcode or None
        # Post offices arrive uppercase (ESPOO, HELSINGFORS): title-case them.
        item["city"] = city_src.strip().title() if city_src and city_src.strip() else None
        item["country"] = "FI"

    def _clean_located_value(self, located: str | None, city_src: str | None) -> str | None:
        # Located leftovers that name no venue: registry boilerplate from
        # slash tails, bare area-type words and municipality duplicates.
        if not located:
            return None
        if located[0].islower():
            located = self._cap_first(located)
        if re.search(r"-palvelun järjestämispaikka", located):
            # Registry boilerplate leaked into a slash tail
            # ("Kyläryhmä -palvelun järjestämispaikka, Virolahti 2"):
            # the sub-unit head is the venue, the rest is record text.
            self._count("name/slash_tail_registry")
            located = re.sub(r"\s*-palvelun järjestämispaikka.*$", "", located).strip(" ,") or None
        if located and located.strip().casefold() in ("ulkoilusaari", "ulkoilusaaret"):
            # Bare outdoor-island type words locate nothing: the head
            # ("Bylandet", "Iso Vasikkasaari") already names the island.
            self._count("name/bare_island_located")
            located = None
        if located and located.strip().upper() in ("OYS", "TYKS", "HUS", "TAYS", "KYS"):
            # Hospital-district acronyms operate the unit; they name no venue.
            self._count("name/located_acronym")
            located = None
        if city_src and located and located.casefold() == city_src.strip().casefold():
            # A venue duplicating the municipality is not a venue.
            self._count("name/located_is_city")
            located = None
        if city_src and located:
            # Municipality segments inside the venue repeat the city field
            # ("Hannes, Hämeenlinna, ..."): the venue reads without them.
            city_cf = city_src.strip().casefold()
            segs = [s.strip() for s in located.split(",")]
            kept = [s for s in segs if s.casefold() != city_cf]
            if len(kept) != len(segs):
                self._count("name/located_city_dropped")
                located = ", ".join(kept).strip(" ,") or None
        if located:
            desc_stripped = self._strip_ostopalvelu(located).strip(" ,")
            if desc_stripped and desc_stripped != located:
                # Purchased-service descriptors ("..., yhteisöllisen
                # asumisen ostopalvelut") are arrangement text, not venues.
                self._count("name/located_descriptor_dropped")
                located = desc_stripped or None
        return located

    def _apply_slash_operator(self, item: Feature, signed: str, shown: str | None, located: str | None) -> str | None:
        # Explicit operator companies/associations in the signed name name
        # the operator (explicit-in-name beats the maintainer): tails
        # ("Imatra Bowling Center / Imatran keilahalli Oy") are never
        # located venues of their own, dropped heads ("Pilke päiväkodit
        # Oy/ Veturi") still operate. Heads surviving in the applied name
        # stay out: chain brands and org styling keep handling them.
        # Returns the located venue, possibly overridden.
        two_seg = len(signed.split(" / ")) == 2
        slash_tail = None
        if " / " in signed:
            candidate = signed.rsplit(" / ", 1)[1].strip()
            if candidate and self._has_operator_word(candidate):
                slash_tail = candidate
        if slash_tail is not None:
            if two_seg:
                # Two-segment tails are never a located venue of their own;
                # longer tails keep the split's venue (explicit venue halves
                # relocate below, activity halves do not).
                located = None
            if ", " in slash_tail:
                venue, _, org = slash_tail.rpartition(", ")
                if org.strip() and self._has_operator_word(org):
                    # Venue-plus-operator tails ("Iltapäivätoiminta /
                    # Tapanilan urheilukeskus, Tapanilan Erä ry"): only the
                    # association half operates; the venue locates. In longer
                    # tails the venue half relocates only when it names a
                    # place (toimintapaikka/skola/enhet); activity halves
                    # ("Linguajoy Language Club") leave the split venue alone.
                    self._count("operator/slash_tail_split")
                    if (
                        two_seg
                        or self._has_fixture(venue)
                        or re.search(
                            r"(toimintapaikka|toimintakeskus|yksikkö|enhet|skola|keskus|talo)",
                            venue.lower(),
                        )
                    ):
                        located = venue.strip() or None
                    slash_tail = org.strip()
            item["operator"] = slash_tail
            self._count("operator/slash_tail")
            self._apply_operator_tags(item, slash_tail)
        elif "/" in signed:
            head = re.split(r"\s*/\s*", signed, maxsplit=1)[0].strip()
            if (
                head
                and (shown or "")
                and head not in shown
                and self._is_operator_shaped(head)
                and not any(re.search(r"\b" + stem + r"\b", (shown or "").lower()) for stem, _ in self.CHAIN_OPERATORS)
            ):
                # Dropped heads still operate: the company does, not the
                # city maintainer. Surviving heads stay out (chain brands,
                # org styling); units named for a chain ("Päiväkoti Pilke
                # Äppelbo") keep the brand via the org join instead.
                item["operator"] = head
                self._count("operator/slash_head")
                self._apply_operator_tags(item, head)
        return located

    def _apply_naming(self, item: Feature, names: dict[str, str], name: str, city_src: str | None) -> None:
        # Split the Finnish name (venue/host extraction); bureau tails are
        # record metadata stripped before both splitting and categories
        # (an unstripped "Kasvatuksen ja koulutuksen toimiala" would file
        # under SCHOOL via "koulutuksen"). Categories otherwise keep reading
        # the signed form so splits never move a category.
        signed = names.get("fi") or name
        if (tr := self._split_translation(signed)) is not None:
            fi_name, sv_name = tr
            item["name"] = fi_name
            item["extras"]["name:sv"] = sv_name
            item["extras"]["official_name"] = signed
            return
        cleaned = self._clean_name(signed)
        shown, located, official = self._split_name(cleaned, city_src)
        located = self._apply_slash_operator(item, signed, shown, located)
        city_match = (
            re.match(re.escape(city_src.strip()) + r"\s+[–—-]\s+(\S)", shown, flags=re.IGNORECASE) if city_src else None
        )
        if city_match and city_match.group(1).islower():
            # Coverage prefixes repeat the municipality in lowercase
            # ("Jämsä – päivätoimintaa ..."): strip to the service, which
            # the lowercase fix below then capitalizes. Proper compounds
            # ("Salo-Karinan neuvonta-asema") stay whole.
            self._count("name/city_prefix_dropped")
            shown = re.sub(
                r"^" + re.escape(city_src.strip()) + r"\s+[–—-]\s+",
                "",
                shown,
                flags=re.IGNORECASE,
            )
            official = official or signed
        if shown and shown[0].islower():
            # Feed names starting lowercase ("vaatelahjoitus...").
            shown = self._cap_first(shown)
        if city_src:
            dash_city = re.search(r"\s+[–—-]\s+([A-ZÅÄÖ][a-zåäö-]+)\s*$", shown)
            if dash_city and dash_city.group(1).casefold() == city_src.strip().casefold():
                # Dash city tails repeat the municipality ("... - Hollola").
                self._count("name/dash_city_dropped")
                shown = shown[: dash_city.start()].strip()
                official = official or signed
        located = self._clean_located_value(located, city_src)
        item["name"] = shown
        if located:
            item["located_in"] = located
        self._apply_branch(item, signed, shown, official, city_src)
        # official_name holds the unparsed signed form only: when nothing
        # was split or cleaned off, translations of the applied name are
        # name:sv/name:en instead (cf. Auroranportin yhteisöllinen asuminen).
        parsed = bool(official or cleaned != signed)
        if parsed:
            item["extras"]["official_name"] = signed
        self._apply_translations(item, names, shown, signed, city_src)

    def _strip_tr_address_paren(self, cleaned_tr: str) -> str:
        paren_stripped = re.sub(
            r"\s*\([^()]*(" + self.STREET_NUMBERED_ALT + r")\b[^()]*\d[^()]*\)\s*$",
            "",
            cleaned_tr,
        ).strip()
        if paren_stripped and paren_stripped != cleaned_tr:
            # Translated street-address tails ("...(Kymmenedalsgränden 4)")
            # duplicate the address line, never the applied name.
            self._count("name/tr_address_dropped")
            return paren_stripped
        return cleaned_tr

    def _tr_is_operator_city(self, cleaned_tr: str, shown: str | None, signed: str | None) -> bool:
        if (
            re.fullmatch(r"City of\s+[A-ZÅÄÖ][a-zåäö-]+\s*", cleaned_tr, flags=re.IGNORECASE)
            and re.search(r"kaupunki|kaupungin", signed or "", flags=re.IGNORECASE)
            and not re.fullmatch(r"\S+\s+kaupunki", (shown or "").strip(), flags=re.IGNORECASE)
        ):
            # Bare English tails naming the operating city ("City of
            # Vaasa" for applied "...hyvinvointipalvelut" under Vaasan
            # kaupunki) render the operator, never the applied name.
            # Operator data is not joined yet here, so the signed
            # Finnish form carries the evidence instead.
            self._count("name/tr_operator_city_dropped")
            return True
        return False

    TR_COPY_SEP_RE = re.compile(r"[,/()“”\"]+")
    TR_COPY_DASH_RE = re.compile(r"[-–—]+")
    TR_COPY_WS_RE = re.compile(r"\s+")

    @classmethod
    def _tr_same(cls, a: str | None, b: str | None) -> bool:
        # Copies differ by case and separators only ("Vantaa-info" /
        # "Vantaa Info, Korso", parenthesised venue restatements):
        # dashes read as spaces, spaces stay significant so genuine
        # Swedish compounds ("Minervaskolan" for "Minerva skolan") survive.
        if not a or not b:
            return False

        def _norm(s: str) -> str:
            s = cls.TR_COPY_DASH_RE.sub(" ", s.casefold())
            return cls.TR_COPY_WS_RE.sub(" ", cls.TR_COPY_SEP_RE.sub("", s)).strip()

        return _norm(a) == _norm(b)

    def _translation_value(
        self, translation: str, shown: str | None, signed: str | None, located: str | None
    ) -> str | None:
        # Cleaned translation of the applied name, or None when the row
        # carries no valid translation (copies, venues, operator cities).
        cleaned_tr = re.sub(r"\s*\d+\*\s*$", "", translation).strip()
        cleaned_tr = self.COORD_TAIL_RE.sub("", cleaned_tr).strip()
        cleaned_tr = self._strip_tr_address_paren(cleaned_tr)
        cleaned_tr = self._strip_fi_duplicates(cleaned_tr, shown, signed, located)
        if "/" in cleaned_tr:
            split_tr = self._split_bilingual(cleaned_tr, shown, signed, located)
            if split_tr is None:
                return None
            cleaned_tr = split_tr
        if self._tr_is_operator_city(cleaned_tr, shown, signed):
            return None
        if (
            cleaned_tr
            and not self._tr_same(cleaned_tr, shown)
            and not self._tr_same(cleaned_tr, signed)
            and not (located and cleaned_tr == located and located in (signed or ""))
        ):
            # An untranslated copy of the Finnish-signed venue is
            # not a translation ("Leikkipuisto Jakomäki" as en).
            return cleaned_tr
        return None

    def _apply_translations(
        self, item: Feature, names: dict[str, str], shown: str | None, signed: str | None, city: str | None = None
    ) -> None:
        # Feed translations describe the applied service (Tykslab for
        # Laboratorio): always name:sv/name:en so renderers see them.
        # A copy of the signed form is not a translation
        # ("Steinergymnasiet (...)" in fi/sv/en alike). Rating
        # artifacts ("... 1*") strip off; bilingual pairs split.
        for lang in ("sv", "en"):
            translation = names.get(lang)
            if translation and not self._tr_same(translation, shown) and not self._tr_same(translation, signed):
                if (value := self._translation_value(translation, shown, signed, item.get("located_in"))) is not None:
                    item["extras"][f"name:{lang}"] = value

    def _positional_comma_keep(self, cleaned_tr: str, shown: str | None, signed: str | None) -> str:
        # Shared positional comma-tail drop: translation segments whose Finnish
        # counterparts fell out of the applied name drop, so the applied name's
        # rendering stays. Both the general and the located-venue passes share
        # these shapes (the latter additionally requires a located venue).
        # Slash-split rows with matching segment counts align by slash
        # below instead: comma alignment across a slash-joined chain
        # keeps only the host tail (Ruuti). Mismatched counts keep the
        # comma path, which alone trims them correctly.
        if "/" in (signed or "") and "/" in cleaned_tr:
            fi_slash = [seg for seg in re.split(r"\s*/\s*", signed or "") if seg.strip()]
            tr_slash = [seg for seg in re.split(r"\s*/\s*", cleaned_tr) if seg.strip()]
            if len(fi_slash) == len(tr_slash):
                return cleaned_tr
        fi_segs = [s.strip() for s in (signed or "").split(",")]
        tr_segs = [s.strip() for s in cleaned_tr.split(",")]
        if (
            len(fi_segs) == len(tr_segs)
            and len(tr_segs) >= 2
            and not re.search(r",\s*[A-ZÅÄÖ][a-zåäö-]+\s*$", shown or "")
        ):
            shown_parts = [s.strip().casefold() for s in (shown or "").split(",")]
            kept = [t for t, f in zip(tr_segs, fi_segs) if f.strip().casefold() in shown_parts]
            if kept and len(kept) < len(tr_segs):
                cleaned_tr = ", ".join(kept)
        return cleaned_tr

    def _tr_commas_positional(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        if "," in cleaned_tr and "," in (signed or ""):
            cleaned_tr = self._positional_comma_keep(cleaned_tr, shown, signed)
        return cleaned_tr

    def _tr_commas_street(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        street_stripped = re.sub(r",\s*\S*(?:" + self.STREET_NUMBERED_ALT + r")\s+\d+\s*$", "", cleaned_tr).strip()
        if street_stripped and street_stripped != cleaned_tr:
            # Trailing street tails moved to the address ("...,
            # Nervanderinkatu 3"): the name translation stays.
            return street_stripped
        return cleaned_tr

    def _tr_commas_fi_forms(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        for form in dict.fromkeys([s for s in (shown, signed, located) if s]):
            cleaned_tr = re.sub(r"\s*\(" + re.escape(form) + r"\)", "", cleaned_tr).strip()
            if " / " not in cleaned_tr:
                head, sep, rest = cleaned_tr.partition(form)
                if sep and not head.strip() and rest and not rest.strip()[0].isalnum():
                    # Leading duplicate ("Aninkaisten koulu (...) Gym A"):
                    # the venue repeats the split-off Finnish name.
                    cleaned_tr = rest.strip(" ,–—-/")
                    if re.fullmatch(r"\([^(),]*\)", cleaned_tr) and not self._paren_cognate(cleaned_tr, form):
                        # Bare descriptor parens ("Päiväkoti Lyyra (private
                        # ECEC centre)"): the row copied the Finnish name,
                        # the paren is not a translation. Parens with commas
                        # are translation twins ("(Turku Lyceum, Kärsämäki
                        # Unit)") and stay, as do parens cognate with the
                        # head ("(Sibbo teater)" for "Sipoon teatteri").
                        self._count("name/tr_descriptor_dropped")
                        cleaned_tr = ""
        return cleaned_tr

    def _tr_commas_located(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        if located and "," in cleaned_tr and "," in (signed or ""):
            # Trailing comma tails duplicating the located venue
            # ("Daghemskök, Päiväkoti Jollas", "Skolrestaurang, Pasilan
            # peruskoulu"): positional match against the signed form, so
            # translated host copies ("Daycare Jollas") drop too. Stranded
            # comma-fragments in the shown name mark a mis-split: skip.
            cleaned_tr = self._positional_comma_keep(cleaned_tr, shown, signed)
        return cleaned_tr

    def _strip_tr_commas(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        # Comma tails duplicating split-off content drop positionally:
        # located venues, municipality tails and street tails repeat
        # emitted tags, so the applied name's rendering stays. Exact
        # Finnish duplicates (parenthesised or leading copies) drop too;
        # the translated rest stays verbatim. Ordered transform pipeline:
        # each stage rewrites the string for the next.
        for transform in (
            self._tr_commas_positional,
            self._tr_commas_street,
            self._tr_commas_fi_forms,
            self._tr_commas_located,
        ):
            cleaned_tr = transform(cleaned_tr, shown, signed, located)
        return cleaned_tr

    @staticmethod
    def _paren_cognate(cleaned_tr: str, form: str) -> bool:
        # Parens translating the head share a word stem with it ("Sibbo
        # teater" for "Sipoon teatteri"); descriptors ("private ECEC
        # centre" for "Päiväkoti Lyyra") share nothing.
        paren_words = re.findall(r"[A-Za-zåäöÅÄÖ]{4,}", cleaned_tr)
        head_words = re.findall(r"[A-Za-zåäöÅÄÖ]{3,}", form or "")
        return any(p[:3].casefold() == h[:3].casefold() for p in paren_words for h in head_words if len(p) >= 4)

    def _tr_align_first_segment(
        self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None
    ) -> str:
        if (
            shown
            and shown.strip() != (signed or "").strip()
            and "," in cleaned_tr
            and (signed or "")
            and shown.strip() == (signed or "").split(",")[0].strip()
            and len(cleaned_tr.split(",")) >= 2
        ):
            # Tails dropped from the Finnish name drop from translations too:
            # the applied name is the first comma segment ("Apuvälinelainaamo"
            # from "..., Raisio, Rusko"), so its translation leads as well.
            return cleaned_tr.split(",")[0].strip()
        return cleaned_tr

    def _tr_align_word_tail(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        if (
            shown
            and shown.strip() != (signed or "").strip()
            and "," not in cleaned_tr
            and "/" not in cleaned_tr
            and (signed or "")
        ):
            # Venue-prefixed translations without delimiters ("Röylän koulu
            # skridskobana" for applied "Luistelukenttä"): word-align with
            # the signed form and keep the applied tail words.
            fi_words = (signed or "").split()
            tr_words = cleaned_tr.split()
            shown_words = shown.split()
            if len(tr_words) == len(fi_words) and len(fi_words) > len(shown_words) >= 1:
                if [w.casefold() for w in fi_words[len(fi_words) - len(shown_words) :]] == [
                    w.casefold() for w in shown_words
                ]:
                    return " ".join(tr_words[len(tr_words) - len(shown_words) :])
        return cleaned_tr

    def _tr_align_venue_drop(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        if (
            cleaned_tr
            and shown
            and (signed or "")
            and "/" in (signed or "")
            and "/" not in cleaned_tr
            and "," not in cleaned_tr
            and located
            and cleaned_tr not in (shown, signed)
        ):
            # Single-segment translations naming the venue instead of the
            # applied name ("Käpylä sports park" for applied "Opastuspiste"
            # at "Käpylän liikuntapuisto"): no valid translation is
            # available, so drop rather than misrender the venue as the POI.
            loc_first = located.split()[0].rstrip("n").casefold()
            if cleaned_tr.split()[0].casefold() == loc_first and loc_first:
                return ""
        return cleaned_tr

    def _strip_tr_alignment(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        # First-segment, word-aligned and venue-naming translations reduce
        # to (or drop for) the applied name. Ordered transform pipeline:
        # each stage rewrites the string for the next.
        for transform in (self._tr_align_first_segment, self._tr_align_word_tail, self._tr_align_venue_drop):
            cleaned_tr = transform(cleaned_tr, shown, signed, located)
        return cleaned_tr

    def _strip_fi_duplicates(self, cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        # Exact Finnish duplicates ride along in feed translations
        # ("Korsverk (Ristikko)", "Aninkaisten koulu (Aninkainen
        # School) Gym A"): parenthesised or leading copies of the
        # applied/signed/venue name drop; the translated rest stays
        # verbatim (parens around translations are the feed's own).
        # Comma tails duplicating split-off content drop positionally:
        # located venues ("Daghemskök, Päiväkoti Jollas"), municipality
        # tails ("Socialbyrå, S:t Karins") and street tails
        # ("Parkeringbiljettautomat 99, Nervanderinkatu 3") repeat
        # emitted tags, so the applied name's rendering stays.
        cleaned_tr = self._strip_tr_commas(cleaned_tr, shown, signed, located)
        cleaned_tr = self._strip_tr_alignment(cleaned_tr, shown, signed, located)
        return re.sub(r"\s{2,}", " ", cleaned_tr).strip()

    @staticmethod
    def _split_bilingual(
        cleaned_tr: str, shown: str | None, signed: str | None, located: str | None = None
    ) -> str | None:
        # Bilingual feed translations ("Sodanajan naisen
        # muistomerkki / Memorial to Women in Times of War"):
        # segments repeating the applied/signed Finnish name
        # drop; "..."-truncated prefixes of them drop too
        # ("Filosofia, lääketiede..."); multi-name translations
        # ("Sibbo Institut / Nickby instituthuset") stay verbatim,
        # full copies skip. Slashes split either spaced or bare, but a
        # segment only drops on an exact or truncated-fi match, so
        # single names with slashes ("Geo/on", "24/7") stay whole.
        # Slash twins follow the split positionally: segments whose
        # signed-form counterpart is the located venue (or the
        # official-only twin) drop, so the applied name's rendering
        # stays ("Sandkajen", "Volleybollplan").
        parts = [s.strip() for s in re.split(r"\s*/\s*", cleaned_tr)]
        parts = [s for s in parts if s]
        fi_parts = [s.strip() for s in re.split(r"\s*/\s*", signed or "") if s.strip()]
        # Stranded comma-fragments in the shown name ("..., Helsingin")
        # mark a mis-split: never trust positional alignment on them.
        positional = (
            len(fi_parts) == len(parts)
            and len(parts) >= 2
            and bool(shown)
            and "/" not in (shown or "")
            and not re.search(r",\s*[A-ZÅÄÖ][a-zåäö-]+\s*$", shown or "")
        )
        if (
            not positional
            and shown
            and "/" not in shown
            and "/" in cleaned_tr
            and located
            and any(s == located for s in parts)
        ):
            # Single-segment applied names with multi-segment translations:
            # exact located copies drop ("Röylän koulu / Ice-skating field"
            # for applied "Luistelukenttä").
            parts = [s for s in parts if s != located]
            cleaned_tr = " / ".join(parts)
            fi_parts = [s.strip() for s in re.split(r"\s*/\s*", signed or "") if s.strip()]
        rest = []
        for i, s in enumerate(parts):
            if PtvFISpider._tr_same(s, shown) or PtvFISpider._tr_same(s, signed):
                continue
            if s.endswith("...") and len(s) > 6:
                base = s[:-3].strip().casefold()
                if any((form or "").strip().casefold().startswith(base) for form in (shown, signed)):
                    continue
            if positional:
                counterpart = fi_parts[i]
                located_parts = [seg.strip() for seg in re.split(r"\s*/\s*", located or "") if seg.strip()]
                if located and (
                    counterpart in located_parts or any(counterpart.startswith(lp + ",") for lp in located_parts)
                ):
                    continue
                if counterpart.endswith("..") and counterpart.casefold() != (shown or "").casefold():
                    # Feed-truncated operator tails ("... / Villiruu..."):
                    # truncation artifacts on non-name segments drop.
                    continue
                if not located and counterpart != shown and counterpart in (signed or ""):
                    continue
            rest.append(s)
        if len(rest) <= 1:
            # A lone surviving truncated Finnish copy ("...Mies..") is not
            # a translation; longer chains keep the lead-segment fallback
            # below instead of degrading to a verbatim chain.
            rest = [
                s
                for s in rest
                if not (
                    s.endswith("..")
                    and not s.endswith("...")
                    and len(s) > 6
                    and any(
                        (form or "").strip().casefold().startswith(s.rstrip(".").strip().casefold())
                        for form in (shown, signed, *fi_parts)
                    )
                )
            ]
        if not rest:
            return None
        if len(rest) < len(parts) and len(rest) == 1:
            return rest[0]
        if (
            len(rest) == len(parts)
            and len(parts) > 1
            and shown
            and "/" not in shown
            and "/" in cleaned_tr
            and not re.search(r",\s*[A-ZÅÄÖ][a-zåäö-]+\s*$", shown or "")
        ):
            # Translated venue/operator tails with no exact Finnish copy
            # ("After-school activities / Helsinki Christian School /
            # Association of ..."): the applied name leads. Stranded
            # comma-fragments in the shown name mark a mis-split: skip.
            return rest[0]
        return cleaned_tr

    def _apply_social_for(self, item: Feature, names: dict[str, str], name: str) -> None:
        # Elderly-targeted social facilities carry their clientele; senior
        # gyms carry theirs (novel fitness_centre:for tag, user-approved).
        cleaned_fi = self._clean_name(names.get("fi") or name)
        senior = any(
            stem in cleaned_fi.lower()
            for stem in ("ikäihmis", "ikäänty", "vanhus", "seniori", "eläkeläis", "pensionär")
        )
        if self._tag(item, "amenity") == "social_facility" and "social_facility:for" not in (item.get("extras") or {}):
            if senior:
                self._count("category/for_senior")
                item["extras"]["social_facility:for"] = "senior"
            return
        if self._tag(item, "leisure") == "fitness_centre" and "fitness_centre:for" not in (item.get("extras") or {}):
            if senior:
                self._count("category/for_senior_gym")
                item["extras"]["fitness_centre:for"] = "senior"

    def _communal_housing(self, channel: dict) -> bool:
        # Communal-housing services ("Sosiaalihuoltolain mukainen
        # yhteisöllinen asuminen") name a care home, whatever proper-noun
        # park or desk the name tier read.
        if any("yhteisöllinen asuminen" in (s or "").lower() for s in self._service_names(channel)):
            return True
        return any("yhteisöllinen asuminen" in v.lower() for v in self._ontology_names(channel))

    def _maybe_upgrade_housing(self, item: Feature, channel: dict, category: Categories | None) -> Categories | None:
        # Supported housing beats diagnosis even when the name tier
        # filed bare social ("Onnikoti Apila", "Tervahovin asunnot"
        # via onto): upgrade to assisted living. Rows that already carry
        # a specific subtype (group homes, nursing homes) keep it.
        # Offices, clinics and schools never upgrade from feed wording.
        # Proper-noun parks over care homes ("Attendo Puistomäki" with a
        # communal-housing service) upgrade to bare social instead.
        if category == Categories.SOCIAL_FACILITY and self._supported_housing(channel):
            extras = item.get("extras") or {}
            if not extras.get("social_facility"):
                self._count("category/supported_housing_upgrade")
                apply_category(Categories.ASSISTED_LIVING, item)
                return Categories.ASSISTED_LIVING
            self._count("category/supported_housing_kept")
        if category == Categories.LEISURE_PARK and self._communal_housing(channel):
            self._count("category/park_housing_upgrade")
            apply_category(Categories.SOCIAL_FACILITY, item)
            (item.get("extras") or {}).pop("leisure", None)
            return Categories.SOCIAL_FACILITY
        return category

    def _parse_gate(self, channel: dict) -> tuple[dict[str, str], str] | None:
        # Type, status, id and name gates: drop non-locations, unpublished rows,
        # id-less rows (downstream keys on channel["id"]), nameless rows and
        # non-place names.
        if not channel.get("id"):
            self._count("dropped/no_id")
            return None
        if channel.get("serviceChannelType") != "ServiceLocation":
            self._count("dropped/type")
            return None
        if channel.get("publishingStatus") != "Published":
            self._count("dropped/unpublished")
            return None
        names = self._names(channel)
        name = names.get("fi") or names.get("sv") or names.get("en")
        if not name:
            name = next((v for v in names.values() if v), None)
        if not name:
            self._count("dropped/no_name")
            return None
        if reason := self._is_dropped_name(names.get("fi") or name):
            self._count("dropped/" + reason)
            return None
        return names, name

    def _parse_place(self, channel: dict) -> tuple[dict, str | None, tuple[float, float] | None, str | None] | None:
        # Visit address (street, postcode, coordinates, municipality):
        # drop postal-only rows and mobile units; coordless rows are kept
        # (the pipeline strips bad geometry but keeps the item).
        address = self._visit_address(channel)
        if address is None:
            self._count("dropped/postal_only")
            return None
        street = address.get("streetAddress") or {}
        postcode = (street.get("postalCode") or "").strip()
        office = self._lang_value((street.get("postOffice") or []), "fi", "sv", "en")
        if postcode == "00000" or (office or "").upper() in ("TUNTEMATON", "OKÄND"):
            # Register rows without a real visit place (mobile units).
            self._count("dropped/non_place/mobile_address")
            return None
        coords = self._coords(street)
        if coords is None:
            self._count("address/no_coords_kept")
        city_src = self._city_src(street, channel, office)
        if office and self._post_city(office) != office.strip():
            # Station-village post-office names are noted, not refiled.
            self._count("address/postoffice_station")
        return street, postcode, coords, city_src

    def _parse_category(self, item: Feature, channel: dict, names: dict[str, str], name: str) -> Categories | None:
        # Category dispatch (table, rescue tiers, extras-only) plus the
        # supported-housing upgrade and the senior clientele tag.
        category, extra = self._category(self._clean_name(names.get("fi") or name))
        if category is None:
            if extra:
                if extra == {"place": "island"} and self._has_art_service(channel):
                    # Artworks titled like islands ("Saari" with Julkinen
                    # taide services) are art, not islands: rescue instead.
                    self._count("category/island_art_rescue")
                    category = self._resolve_fallback_category(item, channel)
                else:
                    # Placement-only tags (squares, youth centres) need no POI category.
                    for key, value in extra.items():
                        item["extras"][key] = value
                    self._count("category/extras_only")
            else:
                category = self._resolve_fallback_category(item, channel)
        else:
            self._count("category/" + category.name)
            apply_category(category, item)
            for key, value in (extra or {}).items():
                item["extras"][key] = value
        category = self._maybe_upgrade_housing(item, channel, category)
        # Category lands before naming so branch/operator demotion read it.
        self._apply_social_for(item, names, name)
        return category

    def parse_channel(self, channel: dict) -> Feature | None:
        gated = self._parse_gate(channel)
        if gated is None:
            return None
        names, name = gated
        placed = self._parse_place(channel)
        if placed is None:
            return None
        street, postcode, coords, city_src = placed

        item = Feature()
        item["ref"] = str(channel["id"])
        item["extras"]["ref:PTV"] = str(channel["id"])
        item["extras"]["source"] = "https://www.suomi.fi/palvelut/palvelupiste/" + str(channel["id"])
        modified = (channel.get("modified") or "").strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", modified):
            # The Suomi.fi "Päivitetty" date: record freshness per row.
            item["extras"]["check_date"] = modified[:10]
        category = self._parse_category(item, channel, names, name)
        self._apply_naming(item, names, name, city_src)

        self._apply_address(item, street, postcode, city_src)
        if coords is not None:
            item["lon"], item["lat"] = coords

        self._apply_contact(item, channel)

        hours = self._hours(channel, category)
        rendered = hours.as_opening_hours() if hasattr(hours, "as_opening_hours") else hours
        if rendered:
            item["opening_hours"] = hours
        return item
