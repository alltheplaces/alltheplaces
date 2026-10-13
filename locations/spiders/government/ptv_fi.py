import re
from typing import Iterable
from urllib.parse import unquote, urlencode

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.licenses import Licenses

# Finnish Service Catalogue (Palvelutietovaranto, PTV), api.palvelutietovaranto.suomi.fi.
# DVV's CC0 national registry of public-sector services: municipalities, wellbeing
# counties and state agencies describe services, ServiceLocation channels are the
# physical visit points (~38k nationally). Complements helsinki_servicemap_fi, which
# is richer per record (WGS84, Hauki hours, mapped taxonomy) but metro-only and
# CC-BY-4.0; PTV is thinner (20-40% hours, user-entered TM35FIN coords) but national
# and CC0. Different refs (UUID vs Servicemap int), so overlap duplicates by design:
# never conflate across spiders, never exclude here because a brand spider exists.
#
# Crawl: 38 id-list pages (?page=N, 1000/page) then batched detail fetches via
# /list?guids=<comma-joined, max ~100> (~380 calls). The full-detail area endpoint
# pages at 4/page and is not used. v11 retires 04/2027; v12 needs an API key.
# PTV latitude/longitude fields are TM35FIN northing/easting, not WGS84.


class PtvFISpider(Spider):
    name = "ptv_fi"
    allowed_domains = ["api.palvelutietovaranto.suomi.fi"]

    dataset_attributes = Licenses.CC0.value

    api_base_url = "https://api.palvelutietovaranto.suomi.fi/api/v11"
    page_size = 1000
    # 40 guids per detail call: 100-guid URLs trip Scrapy's 2083-char
    # urllength middleware and are silently dropped (measured).
    batch_size = 40

    _transformer = Transformer.from_crs(3067, 4326, always_xy=True)

    DAY_MAP = {
        "MONDAY": "Mo",
        "TUESDAY": "Tu",
        "WEDNESDAY": "We",
        "THURSDAY": "Th",
        "FRIDAY": "Fr",
        "SATURDAY": "Sa",
        "SUNDAY": "Su",
    }

    # Road furniture, institutional kitchens, bookmobiles and mobile/outreach
    # services are not visitable fixed POIs (cf. service-map excluded subtrees).
    MOBILE_RE = re.compile(r"(etsivä|liikkuva|hoitoauto|palveluauto|auto$)")
    TRACK_RE = re.compile(r"\b(kuntorata|kuntopolku|latu|luontopolku|retkeilyreitti|hiihtolatu|pururata)\b")
    KM_RE = re.compile(r"\d\s*km\b")
    KITCHEN_INFIX = ("päiväkoti", "koulu", "palvelukeskus", "hoiva", "sairaala", "tuotanto")

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
        ("päiväkoti", Categories.KINDERGARTEN, None),  # Päiväkoti (daycare)
        ("pilke", Categories.KINDERGARTEN, None),  # Pilke (private daycare chain)
        ("norlandia", Categories.KINDERGARTEN, None),  # Norlandia (private daycare chain)
        ("päiväkodin", Categories.KINDERGARTEN, None),  # Päiväkodin (daycare, genitive)
        ("esiopetus", Categories.KINDERGARTEN, None),  # Esiopetus (preschool)
        ("perhepäivähoito", Categories.KINDERGARTEN, None),  # Perhepäivähoito (family daycare)
        ("perhepäivähoitaja", Categories.KINDERGARTEN, None),  # Perhepäivähoitaja (family childminders)
        ("daghem", Categories.KINDERGARTEN, None),  # Daghem (daycare in Swedish)
        ("dagvård", Categories.KINDERGARTEN, None),  # Dagvård (daycare in Swedish)
        ("ryhmis", Categories.KINDERGARTEN, None),  # Ryhmis (family daycare)
        ("dagis", Categories.KINDERGARTEN, None),  # Dagis (daycare in Swedish)
        ("daycare", Categories.KINDERGARTEN, None),  # Daycare (daycare in English)
        ("toddler", Categories.KINDERGARTEN, None),  # Toddler (toddler groups)
        ("preschool", Categories.KINDERGARTEN, None),  # Preschool (preschool in English)
        ("kindergarten", Categories.KINDERGARTEN, None),  # Kindergarten (international daycare)
        ("school", Categories.SCHOOL, None),  # School (schools in English)
        ("oikeusapu", Categories.OFFICE_LAWYER, None),  # Oikeusapu (legal-aid offices)
        ("käräjä", Categories.COURTHOUSE, None),  # Käräjä (courts)
        ("hovioikeus", Categories.COURTHOUSE, None),  # Hovioikeus (courts of appeal)
        ("oikeustiede", Categories.COLLEGE, None),  # Oikeustiede (university law faculties, not courts)
        ("asumisoikeus", Categories.OFFICE_COMPANY, None),  # Asumisoikeus Oy (housing-right companies)
        ("oikeuspsykiatr", Categories.CLINIC, None),  # Forensic psychiatry units
        ("oikeuspsykolog", Categories.CLINIC, None),  # Forensic psychology units
        ("oikeus", Categories.COURTHOUSE, None),  # Oikeus (courts: supreme, insurance, administrative)
        ("kanslia", Categories.OFFICE_GOVERNMENT, None),  # Kanslia (admin offices)
        ("kansli", Categories.OFFICE_GOVERNMENT, None),  # Kansli (admin offices in Swedish)
        ("stadshus", Categories.OFFICE_GOVERNMENT, None),  # Stadshus (city halls in Swedish)
        ("kommunhus", Categories.OFFICE_GOVERNMENT, None),  # Kommunhus (municipal houses in Swedish)
        ("suunnittelu", Categories.OFFICE_GOVERNMENT, None),  # Suunnittelu (planning offices)
        ("psykiatrinen palveluasuminen", Categories.SOCIAL_FACILITY, None),  # Psychiatric housing, not wards
        ("psykiatrinen sairaala", Categories.HOSPITAL, None),  # Psychiatric hospitals
        ("psykiatriasairaala", Categories.HOSPITAL, None),  # Psychiatric hospitals, compound
        ("psykiatri", Categories.CLINIC, None),  # Psykiatri (psychiatry)
        ("nuorten mielenterveys", Categories.CLINIC, None),  # Youth mental-health services
        ("nuorten päihde", Categories.CLINIC, None),  # Youth addiction services
        ("kohtaamispaikka", Categories.COMMUNITY_CENTRE, None),  # Kohtaamispaikka (meeting places outrank clientele)
        ("tukiasunto", Categories.ASSISTED_LIVING, None),  # Tukiasunto (supported housing)
        ("tukiasunnot", Categories.ASSISTED_LIVING, None),  # Tukiasunnot (supported housing, plural)
        ("tuettu asumi", Categories.ASSISTED_LIVING, None),  # Tuettu asuminen (supported housing)
        ("tukiasuminen", Categories.ASSISTED_LIVING, None),  # Tukiasuminen (support housing)
        ("mielenterveystyö", Categories.CLINIC, None),  # Mielenterveystyö (mental-health work)
        ("nuorisoasema", Categories.OFFICE_GOVERNMENT, None),  # Nuorisoasema (youth service stations)
        ("nuorisotila", None, {"amenity": "youth_centre"}),  # Nuorisotila (youth rooms)
        ("nuorisotalo", None, {"amenity": "youth_centre"}),  # Nuorisotalo (youth centres)
        ("nuokkari", None, {"amenity": "youth_centre"}),  # Nuokkari (youth hangouts)
        ("ungdomslokal", None, {"amenity": "youth_centre"}),  # Ungdomslokal (youth rooms in Swedish)
        ("ungdomsgård", None, {"amenity": "youth_centre"}),  # Ungdomsgård (youth centres in Swedish)
        ("järjestämispaikka", Categories.COMMUNITY_CENTRE, None),  # Järjestämispaikka (activity venues)
        ("nuorisokoti", Categories.SOCIAL_FACILITY, {"social_facility": "group_home"}),  # Nuorisokoti (youth homes)
        ("nuoriso", Categories.COMMUNITY_CENTRE, None),  # Nuoriso (youth centres)
        ("nuorten", Categories.COMMUNITY_CENTRE, None),  # Nuorten (youth rooms)
        ("iltapäivä", Categories.COMMUNITY_CENTRE, None),  # Iltapäivä (after-school clubs)
        ("musiikkiopisto", Categories.MUSIC_SCHOOL, None),  # Musiikkiopisto (music schools)
        ("konservatorio", Categories.MUSIC_SCHOOL, None),  # Konservatorio (conservatories)
        ("hammashoito", Categories.DENTIST, None),  # Hammashoito (dental care)
        ("hammashoidon", Categories.DENTIST, None),  # Hammashoidon (dental care, genitive)
        ("hammashoitola", Categories.DENTIST, None),  # Hammashoitola (dental clinics)
        ("suun perusterveydenhuolto", Categories.DENTIST, None),  # Suun perusterveydenhuolto (oral primary care)
        ("suun terveydenhuolto", Categories.DENTIST, None),  # Suun terveydenhuolto (oral health care)
        ("eläinlääkäri", Categories.VETERINARY, None),  # Eläinlääkäri (veterinarians)
        ("löytöeläi", None, {"amenity": "animal_shelter"}),  # Löytöeläimet (found-animal shelters)
        ("löytökiss", None, {"amenity": "animal_shelter"}),  # Löytökissat (found cats)
        ("kissatalo", None, {"amenity": "animal_shelter"}),  # Kissatalo (cat shelters)
        ("eläinsuojelu", Categories.OFFICE_GOVERNMENT, None),  # Eläinsuojelu (animal-protection desks)
        ("terveyspalvelu", Categories.CLINIC, None),  # Terveyspalvelu (health services)
        ("terveystalo", Categories.CLINIC, None),  # Terveystalo (private clinics)
        ("terveyspiste", Categories.CLINIC, None),  # Terveyspiste (health points)
        ("sote-aseman lähitori", Categories.SOCIAL_FACILITY, None),  # Sote-aseman lähitorit (service desks)
        ("terveysasema", Categories.CLINIC, None),  # Terveysasema (health stations)
        ("terveyskeskus", Categories.CLINIC, None),  # Terveyskeskus (health centres)
        ("sote-asema", Categories.CLINIC, None),  # Sote-asema (wellbeing stations)
        ("fysioterapia", Categories.CLINIC, {"healthcare": "physiotherapist"}),
        ("hyvinvointiasema", Categories.CLINIC, None),
        ("hyvinvointikeskus", Categories.CLINIC, None),  # Hyvinvointikeskus (wellbeing centres)
        (
            "sote-piste",
            Categories.CLINIC,
            None,
        ),  # Sote-piste (wellbeing points)  # Hyvinvointiasema (wellbeing stations)
        ("sotekeskus", Categories.CLINIC, None),  # Sotekeskus (wellbeing centres)
        ("sote-keskus", Categories.CLINIC, None),  # Sote-keskus (wellbeing centres)
        ("soteasema", Categories.CLINIC, None),  # Soteasema (wellbeing stations)
        ("poliklinikka", Categories.CLINIC, None),  # Poliklinikka (outpatient clinics)
        ("synnytys", Categories.CLINIC, None),
        ("naistentauti", Categories.CLINIC, None),  # Naistentauti (women health)
        ("äitiys", Categories.CLINIC, None),  # Äitiys (maternity)  # Synnytys (maternity units)
        ("puheterapia", Categories.CLINIC, {"healthcare": "speech_therapist"}),  # Puheterapia (speech therapy)
        ("klinikka", Categories.CLINIC, None),  # Klinikka (clinics)
        ("poliklinikat", Categories.CLINIC, None),  # Poliklinikat (outpatient clinics, plural)
        ("klinikat", Categories.CLINIC, None),  # Klinikat (clinics, plural)
        ("näytteenotto", Categories.SAMPLE_COLLECTION, None),  # Näytteenotto (sampling points)
        ("näytteenoton", Categories.SAMPLE_COLLECTION, None),  # Näytteenoton (sampling points, genitive)
        ("seulonta", Categories.CLINIC, None),  # Seulonta (health screenings)
        ("laboratorio", Categories.CLINIC, {"healthcare": "laboratory"}),  # Laboratorio (laboratories)
        ("lab", Categories.CLINIC, {"healthcare": "laboratory"}),  # Lab (Tykslab/Fimlab/Islab contract labs)
        ("kuvantaminen", Categories.CLINIC, {"healthcare": "medical_imaging"}),  # Kuvantaminen (imaging)
        ("röntgen", Categories.CLINIC, {"healthcare": "medical_imaging"}),  # Röntgen (x-ray clinics)
        ("rontgen", Categories.MEDICAL_IMAGING, None),
        ("terapia", Categories.CLINIC, None),  # Terapia (therapy centres)
        ("jalkaterapeutti", Categories.CLINIC, {"healthcare": "podiatrist"}),  # Jalkaterapeutti (podiatrists)
        ("terapeutti", Categories.CLINIC, None),  # Terapeutti (therapists)
        ("kirurgia", Categories.CLINIC, None),  # Kirurgia (surgery units)
        ("psykoosi", Categories.CLINIC, None),  # Psykoosi (psychosis wards)
        ("psykologi", Categories.CLINIC, None),  # Psykologi (psychology services)
        ("maankäyttö", Categories.OFFICE_GOVERNMENT, None),  # Maankäyttö (land-use admin)
        ("kaupungin asumispalvelu", Categories.OFFICE_GOVERNMENT, None),  # City housing desks
        ("kunnan asumispalvelu", Categories.OFFICE_GOVERNMENT, None),  # Municipal housing desks
        ("asumispalveluyksikk", Categories.SOCIAL_FACILITY, {"social_facility": "group_home"}),
        ("asumisryhmä", Categories.SOCIAL_FACILITY, {"social_facility": "group_home"}),  # Asumisryhmä (housing groups)
        (
            "asumisyhteisö",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Asumisyhteisö (housing communities)
        ("asumispalvelu", Categories.SOCIAL_FACILITY, None),  # Asumispalvelut (housing services)
        ("mielenterveyskuntoutujien", Categories.SOCIAL_FACILITY, None),  # Client housing beats diagnosis below
        ("mielenterveysasiakkaiden", Categories.SOCIAL_FACILITY, None),  # Client housing beats diagnosis below
        ("mielenterveys", Categories.CLINIC, None),  # Mielenterveys (mental health)
        ("muistikeskus", Categories.CLINIC, None),  # Muistikeskus (memory clinics)
        ("mielialahäiriö", Categories.CLINIC, None),  # Mielialahäiriö (mood disorders)
        ("diabeteskeskus", Categories.CLINIC, None),  # Diabeteskeskus (diabetes centres)
        ("diabeteshoitaja", Categories.CLINIC, {"healthcare": "nurse"}),  # Diabeteshoitaja (diabetes nurses)
        ("apteekki", Categories.PHARMACY, None),  # Apteekki (pharmacies)
        ("apotek", Categories.PHARMACY, None),  # Apotek (pharmacies in Swedish)
        ("tarvikejakelu", Categories.SHOP_MEDICAL_SUPPLY, None),  # Tarvikejakelu (supply distribution)
        ("apuväline", Categories.OFFICE_GOVERNMENT, None),  # Apuväline (assistive-device service points)
        ("vastaanottokeskus", Categories.SOCIAL_FACILITY, None),  # Vastaanottokeskus (reception centres)
        ("jäte", Categories.RECYCLING, None),  # Jäte (waste services)
        ("jätteen", Categories.RECYCLING, None),  # Jätteen (waste services, genitive)
        ("jätte", Categories.RECYCLING, None),  # Jätte- (waste compounds, plural stem)
        ("sosiaalipalvelu", Categories.OFFICE_GOVERNMENT, None),  # Sosiaalipalvelu (social-service desks)
        ("elinkeinopalvelu", Categories.OFFICE_GOVERNMENT, None),  # Elinkeinopalvelut (business-service desks)
        ("elinkeinotoimi", Categories.OFFICE_GOVERNMENT, None),  # Elinkeinotoimi (business-development units)
        ("vastaanotto", Categories.CLINIC, None),  # Vastaanotto (receptions)
        ("vastaanotot", Categories.CLINIC, None),  # Vastaanotot (receptions, plural)
        ("beachvolley", Categories.LEISURE_PITCH, {"sport": "beachvolleyball"}),  # Beachvolley (beach volleyball)
        ("beach volley", Categories.LEISURE_PITCH, {"sport": "beachvolleyball"}),  # Beach volley (spaced)
        ("volley", Categories.LEISURE_PITCH, {"sport": "volleyball"}),  # Volley (volleyball)
        ("huoltorakennus", None, None),  # Huoltorakennus (service buildings): no precise filing, keep generic
        ("koirauimaranta", Categories.LEISURE_DOG_PARK, None),  # Koirauimaranta (dog beaches)
        ("talviuimari", Categories.LEISURE_SWIMMING_AREA, None),  # Talviuimarit (winter swimmers)
        ("talviuimaranta", Categories.LEISURE_SWIMMING_AREA, None),  # Talviuimaranta (winter-swimming beaches)
        ("uimaranta", Categories.NATURAL_BEACH, None),  # Uimaranta (beaches)
        ("uimarannat", Categories.NATURAL_BEACH, None),  # Uimarannat (beaches, plural)
        ("uimapaikka", Categories.NATURAL_BEACH, None),  # Uimapaikka (swimming places)
        ("ulkokuntosali", Categories.LEISURE_FITNESS_STATION, None),  # Ulkokuntosali (outdoor gyms)
        ("ulkokuntoilu", Categories.LEISURE_FITNESS_STATION, None),  # Ulkokuntoilu (outdoor exercise)
        ("lähiliikuntapaikka", Categories.LEISURE_FITNESS_STATION, None),  # Lähiliikuntapaikka (exercise grounds)
        ("kuntoilupaikka", Categories.LEISURE_FITNESS_STATION, None),  # Kuntoilupaikka (exercise grounds)
        ("kuntoilupiste", Categories.LEISURE_FITNESS_STATION, None),  # Kuntoilupisteet (exercise points)
        ("opastuspiste", Categories.TOURISM_INFORMATION, None),  # Opastuspisteet (info points)
        ("kuntoportaat", Categories.LEISURE_FITNESS_STATION, None),  # Kuntoportaat (fitness stairs)
        ("uimahallin", Categories.GYM, None),  # Uimahallin (gym of a swim hall)
        ("uimahalli", Categories.LEISURE_SPORTS_CENTRE, {"sport": "swimming"}),  # Uimahalli (swimming halls)
        ("uintikeskus", Categories.LEISURE_SPORTS_CENTRE, None),  # Uintikeskus (swimming centres)
        ("kuntosali", Categories.GYM, None),  # Kuntosali (gyms)
        ("uimastadion", Categories.LEISURE_SPORTS_CENTRE, None),
        (
            "uima-allas",
            Categories.LEISURE_SPORTS_HALL,
            None,
        ),  # Uima-allas (school pools)  # Uimastadion (swimming stadiums)
        ("maauimala", Categories.LEISURE_SPORTS_CENTRE, None),  # Maauimala (outdoor pools)
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
        ("koripallo", Categories.LEISURE_PITCH, {"sport": "basketball"}),  # Koripallo (basketball)
        (
            "rantalentopallo",
            Categories.LEISURE_PITCH,
            {"sport": "beachvolleyball"},
        ),  # Rantalentopallo (beach volleyball)
        ("lentopallo", Categories.LEISURE_PITCH, {"sport": "volleyball"}),  # Lentopallo (volleyball)
        ("petanque", Categories.LEISURE_PITCH, {"sport": "petanque"}),  # Petanque (petanque courses)
        ("pesäpallo", Categories.LEISURE_PITCH, {"sport": "pesapallo"}),  # Pesäpallo (Finnish baseball)
        ("shakkilauta", Categories.LEISURE_PITCH, {"sport": "chess"}),  # Shakkilauta (outdoor chess boards)
        ("shakkilaudat", Categories.LEISURE_PITCH, {"sport": "chess"}),  # Shakkilaudat (chess boards, plural)
        ("liikuntahalli", Categories.LEISURE_SPORTS_CENTRE, None),
        ("liikuntakeskus", Categories.LEISURE_SPORTS_CENTRE, None),  # Liikuntakeskus (sports centres)
        (
            "ulkoilukeskus",
            Categories.LEISURE_SPORTS_CENTRE,
            None,
        ),  # Ulkoilukeskus (outdoor centres)  # Liikuntahalli (sports halls)
        ("urheiluhalli", Categories.LEISURE_SPORTS_CENTRE, None),
        ("liikuntasali", Categories.LEISURE_SPORTS_HALL, None),  # Liikuntasali (sports halls)
        ("liikuntatilat", Categories.LEISURE_SPORTS_HALL, None),  # Liikuntatilat (sports facilities)
        ("tapahtuma-alue", Categories.EVENTS_VENUE, None),  # Tapahtuma-alue (event grounds)
        ("tapahtumalava", Categories.EVENTS_VENUE, None),  # Tapahtumalava (event stages)
        ("tapahtumatalo", Categories.EVENTS_VENUE, None),  # Tapahtumatalo (event houses)
        ("tapahtumakeskus", Categories.EVENTS_VENUE, None),  # Tapahtumakeskus (event centres)
        ("tapahtumasali", Categories.EVENTS_VENUE, None),  # Tapahtumasali (event halls)
        ("kiipeily", Categories.LEISURE_PITCH, {"sport": "climbing"}),  # Kiipeily (climbing spots)
        ("salibandy", Categories.LEISURE_PITCH, {"sport": "floorball"}),  # Salibandy (floorball)
        ("moottoriurheilu", Categories.LEISURE_PITCH, {"sport": "motor"}),  # Moottoriurheilu (motorsports)
        ("sähly", Categories.LEISURE_PITCH, {"sport": "floorball"}),  # Sähly (floorball)
        ("näyttely", Categories.MUSEUM, None),  # Näyttely (exhibition venues)
        ("kokoelma", Categories.MUSEUM, None),  # Kokoelma (collections)
        ("juhlasali", Categories.EVENTS_VENUE, None),  # Juhlasali (banquet halls)
        ("musiikkisali", Categories.EVENTS_VENUE, None),  # Musiikkisali (concert halls)
        ("monitoimisali", Categories.EVENTS_VENUE, None),  # Monitoimisali (multi-purpose halls)
        ("valtuustosali", Categories.EVENTS_VENUE, None),  # Valtuustosali (council chambers)
        ("lehtilukusali", Categories.LIBRARY, None),  # Lehtilukusali (library reading rooms)
        ("lehtisali", Categories.LIBRARY, None),  # Lehtisali (library reading rooms)
        ("sali", Categories.LEISURE_SPORTS_HALL, None),  # Sali (halls)
        ("jäähalli", Categories.LEISURE_ICE_RINK, None),
        ("keilahalli", Categories.LEISURE_BOWLING_ALLEY, None),  # Keilahalli (bowling halls)
        ("skeittihalli", Categories.LEISURE_SPORTS_CENTRE, {"sport": "skateboard"}),  # Skeittihalli (skate halls)
        ("monitoimihalli", Categories.COMMUNITY_CENTRE, None),  # Monitoimihalli (multipurpose halls)
        ("halli", Categories.LEISURE_SPORTS_HALL, None),  # Halli (halls, compound-final)
        ("auditorio", Categories.EVENTS_VENUE, None),  # Auditorio (auditoriums)
        ("konserttitalo", Categories.EVENTS_VENUE, None),  # Konserttitalo (concert halls)
        ("kongressitalo", Categories.EVENTS_VENUE, None),  # Kongressitalo (congress halls)
        ("palloiluhalli", Categories.LEISURE_SPORTS_HALL, None),  # Palloiluhalli (ball-game halls)
        ("parkour", Categories.LEISURE_PITCH, {"sport": "parkour"}),  # Parkour (parkour areas)
        ("streetworkout", Categories.LEISURE_FITNESS_STATION, None),  # Streetworkout (outdoor gyms)
        ("street workout", Categories.LEISURE_FITNESS_STATION, None),  # Street workout (outdoor gyms, spaced)
        ("paini", Categories.LEISURE_SPORTS_HALL, None),  # Paini (wrestling)
        ("kamppailu", Categories.LEISURE_SPORTS_HALL, None),  # Kamppailu (martial arts)
        ("bowling", Categories.LEISURE_BOWLING_ALLEY, None),  # Bowling (bowling halls)
        ("minigolf", Categories.LEISURE_MINIATURE_GOLF, None),  # Minigolf (miniature golf)
        ("seikkailugolf", Categories.LEISURE_MINIATURE_GOLF, None),
        ("puttiparkki", Categories.LEISURE_MINIATURE_GOLF, None),  # Puttiparkki (putting courses)
        ("frisbeegolf", Categories.LEISURE_DISC_GOLF_COURSE, None),
        ("frisbee", Categories.LEISURE_DISC_GOLF_COURSE, None),  # Frisbee (disc golf)  # Frisbeegolf (disc golf)
        ("discgolf", Categories.LEISURE_DISC_GOLF_COURSE, None),  # Discgolf (disc golf)
        ("golf", Categories.LEISURE_GOLF_COURSE, None),  # Golf (golf courses)
        ("pumptrack", Categories.LEISURE_TRACK, None),  # Pumptrack (pump tracks)  # Jäähalli (ice halls)
        ("pump track", Categories.LEISURE_TRACK, None),  # Pump track (pump tracks, spaced)
        ("luistelukenttä", Categories.LEISURE_ICE_RINK, None),
        ("jääkenttä", Categories.LEISURE_ICE_RINK, None),  # Jääkenttä (ice rinks)
        ("kaukalo", Categories.LEISURE_ICE_RINK, None),  # Kaukalo (hockey rinks)  # Luistelukenttä (skating rinks)
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
        ("soutu", Categories.LEISURE_SPORTS_CENTRE, None),  # Soutu (rowing venues)
        ("melonta", Categories.LEISURE_SPORTS_CENTRE, None),  # Melonta (canoeing venues)
        ("liikuntamylly", Categories.LEISURE_SPORTS_CENTRE, None),  # Liikuntamylly (sports halls)
        ("stadion", Categories.LEISURE_PITCH, None),  # Stadion (stadiums)
        ("skate", Categories.LEISURE_PITCH, {"sport": "skateboard"}),  # Skate (skate parks)
        ("skeitti", Categories.LEISURE_PITCH, {"sport": "skateboard"}),  # Skeitti (skate parks)
        ("leikkipuisto", Categories.LEISURE_PLAYGROUND, None),  # Leikkipuisto (playgrounds)
        ("leikkikerho", Categories.KINDERGARTEN, None),  # Leikkikerho (playgroups)
        ("leikkikoulu", Categories.KINDERGARTEN, None),  # Leikkikoulu (play schools)
        ("leikkipaikka", Categories.LEISURE_PLAYGROUND, None),  # Leikkipaikka (play areas)
        ("leikkikenttä", Categories.LEISURE_PLAYGROUND, None),  # Leikkikenttä (playgrounds)
        ("leikkivä", None, None),  # Leikkivä titles (artworks like Leikkivät karhut): rescue decides
        ("leikki", Categories.LEISURE_PLAYGROUND, None),  # Leikki (play)
        ("keittokatos", Categories.TOURISM_PICNIC_SITE, None),  # Keittokatos (cooking shelters)
        ("kaupungintalon puisto", Categories.LEISURE_PARK, None),  # Kaupungintalon puisto (city-hall park)
        ("grillipaikka", Categories.TOURISM_PICNIC_SITE, None),  # Grillipaikka (BBQ spots)
        ("koira-aitaus", Categories.LEISURE_DOG_PARK, None),  # Koira-aitaus (dog enclosures)
        ("koirametsä", Categories.LEISURE_DOG_PARK, None),  # Koirametsä (dog forests)
        ("lippumyymälä", None, {"shop": "tickets"}),  # Lippumyymälä (ticket shops)
        ("lipunmyynti", None, {"shop": "tickets"}),  # Lipunmyynti (ticket sales)
        ("lippukassa", None, {"shop": "tickets"}),  # Lippukassa (ticket offices)
        ("myymälä", None, {"shop": "yes"}),  # Myymälä (shops)
        ("huvila", None, None),  # Huvila (villas): no precise filing, keep generic
        ("kalastuspaikka", None, {"leisure": "fishing"}),  # Kalastuspaikka (fishing spots, incl. at shores/zoo bays)
        ("kalastuslupa", None, {"leisure": "fishing"}),  # Kalastuslupa-alueet (fishing permit areas)
        ("eläintarha", None, {"tourism": "zoo"}),  # Eläintarha (zoos)
        ("koirapuisto", Categories.LEISURE_DOG_PARK, None),  # Koirapuisto (dog parks)
        ("koiratarha", Categories.LEISURE_DOG_PARK, None),  # Koiratarha (dog yards)
        ("hundpark", Categories.LEISURE_DOG_PARK, None),  # Hundpark (dog parks in Swedish)
        ("koirakäymälä", None, {"amenity": "dog_toilet"}),  # Koirakäymälä (dog toilets)
        ("pysäköinti", Categories.PARKING, None),  # Pysäköinti (parking)
        ("latauspiste", Categories.CHARGING_STATION, None),  # Latauspiste (charging points)
        ("latausasema", Categories.CHARGING_STATION, None),  # Latausasema (charging stations)
        ("juhannussalko", Categories.TOURISM_ARTWORK, None),  # Juhannussalko (midsummer poles)
        ("henkilöstöravintola", Categories.CANTEEN, None),  # Henkilöstöravintola (staff canteens)
        ("henkilöstöosasto", Categories.OFFICE_GOVERNMENT, None),  # Henkilöstöosasto (HR departments)
        ("kouluravintola", Categories.CANTEEN, None),  # Kouluravintola (school canteens)
        ("ruokapalvelu", Categories.CANTEEN, None),  # Ruokapalvelu (food services)
        ("ravintola", Categories.RESTAURANT, None),  # Ravintola (restaurants)
        ("ruokala", Categories.CANTEEN, None),  # Ruokala (canteens)
        ("kenttä", Categories.LEISURE_PITCH, None),  # Kenttä (fields)
        ("miniareena", Categories.LEISURE_SPORTS_HALL, None),  # Miniareena (mini arenas)
        ("areena", Categories.LEISURE_SPORTS_CENTRE, None),  # Areena (arenas)
        ("urheilutalo", Categories.LEISURE_SPORTS_CENTRE, None),  # Urheilutalo (sports buildings)
        ("liikuntatalo", Categories.LEISURE_SPORTS_CENTRE, None),  # Liikuntatalo (sports houses)
        ("liikuntapuisto", Categories.LEISURE_SPORTS_CENTRE, None),  # Liikuntapuisto (sports parks)
        ("kahvila", Categories.CAFE, None),  # Kahvila (cafes)
        ("kahvio", Categories.CAFE, None),  # Kahvio (cafe counters)
        ("urheilukeskus", Categories.LEISURE_SPORTS_CENTRE, None),  # Urheilukeskus (sports centres)
        ("monitoimitila", Categories.COMMUNITY_CENTRE, None),  # Monitoimitila (multipurpose rooms)
        ("kirjasto", Categories.LIBRARY, None),  # Kirjasto (libraries)
        ("lainausasema", Categories.LIBRARY, None),  # Lainausasemat (library branches)
        ("arkisto", Categories.ARCHIVE, None),  # Arkisto (archives)
        ("kansalaisopisto", Categories.COLLEGE, None),  # Kansalaisopisto (civic institutes)
        ("työväenopisto", Categories.COLLEGE, None),  # Työväenopisto (workers' institutes)
        ("kansanopisto", Categories.COLLEGE, None),  # Kansanopisto (folk high schools)
        ("opisto", Categories.COLLEGE, None),
        ("instituutti", Categories.COLLEGE, None),  # Instituutti (institutes)
        ("äänitysstudio", Categories.MUSIC_SCHOOL, None),  # Äänitysstudio (recording studios)
        ("akatemia", Categories.COLLEGE, None),  # Akatemia (academies)
        ("academy", Categories.COLLEGE, None),  # Academy (academies)  # Opisto (institutes)
        ("kampus", Categories.COLLEGE, None),  # Kampus (campuses)
        ("keuda", Categories.COLLEGE, None),  # Keuda (vocational consortium)
        ("redu", Categories.COLLEGE, None),  # REDU (Lapland education consortium)
        ("gymnasi", Categories.SCHOOL, None),  # Gymnasi (gymnasium schools in Swedish, all inflections)
        ("gym", Categories.GYM, None),  # Gym (gyms in English)
        ("fitness", Categories.GYM, None),  # Fitness (fitness centres)
        ("lukio", Categories.SCHOOL, None),  # Lukio (upper secondary schools)
        ("lyseo", Categories.SCHOOL, None),  # Lyseo (lyceums, upper secondary schools)
        ("peruskoulu", Categories.SCHOOL, None),  # Peruskoulu (basic education)
        ("yläaste", Categories.SCHOOL, None),  # Yläaste (upper comprehensive)
        ("ala-aste", Categories.SCHOOL, None),  # Ala-aste (lower comprehensive)
        ("yhtenäiskoulu", Categories.SCHOOL, None),  # Yhtenäiskoulu (comprehensive schools)
        ("förskola", Categories.KINDERGARTEN, None),  # Förskola (preschools in Swedish)
        ("skola", Categories.SCHOOL, None),  # Skola (schools in Swedish)
        ("koulutuskeskus", Categories.COLLEGE, None),  # Koulutuskeskus (training centres)
        ("koulutus", Categories.OFFICE_GOVERNMENT, None),  # Koulutus (education services)
        ("koulutukset", Categories.OFFICE_GOVERNMENT, None),  # Koulutukset (training courses)
        ("uimakoulu", None, None),  # Uimakoulut (swimming lessons): no venue, keep generic
        ("koulumuseo", Categories.MUSEUM, None),  # Koulumuseo (school museums)
        ("koulutoimisto", Categories.OFFICE_GOVERNMENT, None),  # Koulutoimisto (education offices)
        ("koulu", Categories.SCHOOL, None),  # Koulu (schools)
        ("lupapalvelu", Categories.OFFICE_GOVERNMENT, None),  # Lupapalvelu (permit services, also at stations)
        ("erityislupa", Categories.OFFICE_GOVERNMENT, None),  # Erityislupa (special permits, also at stations)
        ("lupa-asi", Categories.OFFICE_GOVERNMENT, None),  # Lupa-asiat (permit matters, also at stations)
        ("poliisi", Categories.POLICE, None),  # Poliisi (police)
        ("tarkastus", Categories.OFFICE_GOVERNMENT, None),  # Tarkastus (inspection desks)
        ("kriisi", Categories.SOCIAL_FACILITY, None),  # Kriisi (crisis services)
        ("tukikeskus", Categories.SOCIAL_FACILITY, None),  # Tukikeskus (support centres)
        ("päivystys", Categories.CLINIC_URGENT, None),  # Päivystys (emergency departments)
        ("päiväsairaala", Categories.CLINIC, None),  # Päiväsairaala (day hospitals)
        ("kliininen", Categories.CLINIC, None),  # Kliininen (clinical units)
        ("potilasasia", Categories.OFFICE_GOVERNMENT, None),  # Potilasasia (patient-ombudsman desks)
        ("keskussairaala", Categories.HOSPITAL, None),  # Keskussairaala (central hospitals)
        ("sairaala", Categories.HOSPITAL, None),  # Sairaala (hospitals)
        ("lähitori", Categories.SOCIAL_FACILITY, None),  # Lähitori (senior service points)
        ("konttori", Categories.OFFICE_COMPANY, None),  # Konttori (head offices)
        ("kehitysyhtiö", Categories.OFFICE_COMPANY, None),  # Kehitysyhtiö (development companies)
        ("yritystalo", Categories.OFFICE_COMPANY, None),  # Yritystalo (business houses)
        ("kiinteistö oy", Categories.OFFICE_COMPANY, None),  # Kiinteistö Oy (property companies)
        ("kuraattori", Categories.SCHOOL, None),  # Kuraattori (school counsellors)
        ("luonnonsuojelualue", Categories.LEISURE_NATURE_RESERVE, None),  # Luonnonsuojelualue (nature reserves)
        ("arboretum", None, {"leisure": "botanical_garden"}),  # Arboretum (arboreta)
        ("erikoismetsä", None, {"natural": "wood"}),  # Erikoismetsä (designated municipal forests)
        ("teatteri", Categories.THEATRE, None),
        ("kirkko", Categories.PLACE_OF_WORSHIP, None),
        ("rukoushuone", Categories.PLACE_OF_WORSHIP, None),  # Rukoushuone (prayer rooms)
        ("raamattuhuone", Categories.PLACE_OF_WORSHIP, None),  # Raamattuhuone (prayer rooms)  # Kirkko (churches)
        ("kappeli", Categories.PLACE_OF_WORSHIP, None),  # Kappeli (chapels)
        ("seurakuntatalo", Categories.COMMUNITY_CENTRE, None),  # Seurakuntatalo (parish halls)
        ("seurakuntakoti", Categories.COMMUNITY_CENTRE, None),  # Seurakuntakoti (parish houses)
        ("seurakuntakeskus", Categories.COMMUNITY_CENTRE, None),  # Seurakuntakeskus (parish centres)
        ("seurakuntatila", Categories.COMMUNITY_CENTRE, None),  # Seurakuntatila (parish premises)
        ("muistomerkki", Categories.TOURISM_ARTWORK, None),
        ("memorial", Categories.TOURISM_ARTWORK, None),  # Memorial (memorials in English)
        ("minnesmärk", Categories.TOURISM_ARTWORK, None),  # Minnesmärke (memorials in Swedish)
        ("galleria", Categories.ARTS_CENTRE, None),  # Galleria (art galleries)
        ("taiteen perusopetus", Categories.ARTS_CENTRE, None),  # Taiteen perusopetus (basic art education)
        ("linnoitus", Categories.TOURISM_ATTRACTION, None),  # Linnoitus (fortresses)  # Muistomerkki (memorials)
        ("lammasaitaus", Categories.TOURISM_ATTRACTION, None),  # Lammasaitaus (sheep enclosures)
        ("monumentti", Categories.TOURISM_ARTWORK, None),  # Monumentti (monuments)
        ("patsas", Categories.TOURISM_ARTWORK, {"artwork_type": "sculpture"}),  # Patsas (statues)
        ("graffiti", Categories.TOURISM_ARTWORK, {"artwork_type": "graffiti"}),  # Graffiti (graffiti walls)
        ("graffitti", Categories.TOURISM_ARTWORK, {"artwork_type": "graffiti"}),  # Graffitti (graffiti variant)
        ("taidekontti", Categories.TOURISM_ARTWORK, None),  # Taidekontti (art containers)
        ("avantouinti", Categories.LEISURE_SWIMMING_AREA, None),  # Avantouinti (winter swimming)
        ("avanto", Categories.LEISURE_SWIMMING_AREA, None),  # Avanto (ice-swimming holes)
        ("talviuinti", Categories.LEISURE_SWIMMING_AREA, None),  # Talviuinti (winter swimming)
        ("luistelu", Categories.LEISURE_ICE_RINK, None),  # Luistelu (skating)
        ("lastenkoti", Categories.SOCIAL_FACILITY, {"social_facility": "group_home"}),  # Lastenkoti (children homes)
        ("ryhmäkoti", Categories.SOCIAL_FACILITY, {"social_facility": "group_home"}),  # Ryhmäkoti (group homes)
        (
            "ryhmäkodit",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Ryhmäkodit (group homes, plural)
        (
            "yhteisöllinen asuminen",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Yhteisöllinen asuminen (communal housing)
        ("palveluasumisyksikkö", Categories.NURSING_HOME, None),  # Palveluasumisyksiköt (service-housing units)
        (
            "asumisyksikkö",
            Categories.SOCIAL_FACILITY,
            {"social_facility": "group_home"},
        ),  # Asumisyksikkö (housing units)
        ("toimintakeskus", Categories.COMMUNITY_CENTRE, None),  # Toimintakeskus (activity centres)
        ("monitoimitalo", Categories.COMMUNITY_CENTRE, None),  # Monitoimitalo (multipurpose houses)
        ("kohtaamispaikka", Categories.COMMUNITY_CENTRE, None),  # Kohtaamispaikka (meeting places)
        ("kerhotalo", Categories.COMMUNITY_CENTRE, None),  # Kerhotalo (clubhouses)
        ("harrastetila", Categories.COMMUNITY_CENTRE, None),  # Harrastetila (hobby premises)
        ("harrastuskeskus", Categories.COMMUNITY_CENTRE, None),  # Harrastuskeskus (hobby centres)
        ("kerhohuone", Categories.COMMUNITY_CENTRE, None),  # Kerhohuone (club rooms)
        ("asukastila", Categories.COMMUNITY_CENTRE, None),  # Asukastilat (resident premises)
        ("4h-kerho", Categories.COMMUNITY_CENTRE, None),  # 4H-kerho (4H children's clubs)
        ("kylätalo", Categories.COMMUNITY_CENTRE, None),  # Kylätalo (village halls)
        ("seurantalo", Categories.COMMUNITY_CENTRE, None),  # Seurantalo (association houses)
        ("työväentalo", Categories.COMMUNITY_CENTRE, None),  # Työväentalo (workers' halls)
        ("kotiseututalo", Categories.COMMUNITY_CENTRE, None),  # Kotiseututalo (heritage houses)
        ("olka-piste", Categories.OFFICE_GOVERNMENT, None),  # OLKA-pisteet (hospital info desks)
        ("yhdistys", Categories.COMMUNITY_CENTRE, None),  # Yhdistys (association houses)
        ("kumppanuustalo", Categories.COMMUNITY_CENTRE, None),  # Kumppanuustalo (partnership houses)
        ("järjestötalo", Categories.COMMUNITY_CENTRE, None),  # Järjestötalo (organisation houses)
        ("yhteisötalo", Categories.COMMUNITY_CENTRE, None),  # Yhteisötalo (community houses)
        ("yhteisökeskus", Categories.COMMUNITY_CENTRE, None),  # Yhteisökeskus (community centres)
        ("kulttuuritalo", Categories.COMMUNITY_CENTRE, None),  # Kulttuuritalo (culture houses)
        ("lastenkulttuurikeskus", Categories.ARTS_CENTRE, None),  # Lastenkulttuurikeskus (children's culture centres)
        ("kulttuurikeskus", Categories.COMMUNITY_CENTRE, None),  # Kulttuurikeskus (culture centres)
        ("kulttuuritila", Categories.COMMUNITY_CENTRE, None),  # Kulttuuritila (culture premises)
        ("yhteisötila", Categories.COMMUNITY_CENTRE, None),  # Yhteisötila (community premises)
        (
            "kokoustila",
            Categories.EVENTS_VENUE,
            None,
        ),  # Kokoustila (meeting rooms)  # Monitoimihalli (multipurpose halls)
        ("neuvottelu", Categories.SOCIAL_FACILITY, None),  # Neuvottelu (negotiation centres, all family-affairs)
        ("poliisiasema", Categories.POLICE, None),  # Poliisiasema (police stations)
        ("pelastusasema", Categories.FIRE_STATION, None),  # Pelastusasema (rescue stations)
        ("vpk", Categories.FIRE_STATION, None),  # VPK (volunteer fire brigades)
        ("palokunta", Categories.FIRE_STATION, None),  # Palokunta (fire brigades)
        ("paloasema", Categories.FIRE_STATION, None),  # Paloasema (fire stations)
        ("linja-autoasema", Categories.BUS_STATION, None),  # Linja-autoasema (bus stations)
        ("bussiasema", Categories.BUS_STATION, None),  # Bussiasema (bus stations)
        ("huoltoasema", None, None),  # Huoltoasema (fuel stations): no precise filing, keep generic
        ("rautatieasema", None, {"railway": "station", "public_transport": "station"}),
        ("ilmailukeskus", None, {"aeroway": "aerodrome"}),  # Ilmailukeskus (sport-aviation fields)
        ("kunnanvirasto", Categories.OFFICE_GOVERNMENT, None),  # Kunnanvirasto (municipal offices)
        ("kaupungintalo", Categories.OFFICE_GOVERNMENT, None),  # Kaupungintalo (city halls)
        ("kaupunginvirasto", Categories.OFFICE_GOVERNMENT, None),  # Kaupunginvirasto (city offices)
        ("office", Categories.OFFICE_GOVERNMENT, None),  # Office (service offices in English)
        ("lautakunta", Categories.OFFICE_GOVERNMENT, None),  # Lautakunta (municipal boards)
        ("valtuusto", Categories.OFFICE_GOVERNMENT, None),  # Valtuusto (councils; youth councils keep community above)
        ("hankinta", Categories.OFFICE_GOVERNMENT, None),  # Hankinta (procurement units)
        ("hankinnat", Categories.OFFICE_GOVERNMENT, None),  # Hankinnat (procurement units, plural)
        ("tonttijako", Categories.OFFICE_GOVERNMENT, None),  # Tonttijako (plot-division desks)
        ("maakuntatalo", Categories.OFFICE_GOVERNMENT, None),  # Maakuntatalo (regional houses)
        ("liikelaitos", Categories.OFFICE_COMPANY, None),  # Liikelaitos (municipal business enterprises)
        ("keskusrekisteri", Categories.OFFICE_GOVERNMENT, None),  # Keskusrekisteri (parish register offices)
        ("kunnantalo", Categories.OFFICE_GOVERNMENT, None),  # Kunnantalo (municipal halls)
        ("hallinto", Categories.OFFICE_GOVERNMENT, None),  # Hallinto (administrations)
        ("virasto", Categories.OFFICE_GOVERNMENT, None),  # Virasto (agencies)
        ("päihde", Categories.CLINIC, None),  # Päihde (substance-abuse care)  # Fysioterapia (physiotherapy)
        ("arviointiyksikkö", Categories.CLINIC, None),  # Arviointiyksikkö (assessment units)
        ("tutkimusyksik", Categories.CLINIC, None),  # Tutkimusyksikkö (examination units, all inflections)
        ("akuuttiosasto", Categories.CLINIC, None),  # Akuuttiosasto (acute wards)
        ("vuodeosasto", Categories.CLINIC, None),  # Vuodeosasto (inpatient wards)
        ("kuntoutusyksikkö", Categories.CLINIC, None),  # Kuntoutusyksikkö (rehabilitation units)
        ("oy:n toimisto", Categories.OFFICE_COMPANY, None),  # Oy:n toimisto (company offices)
        ("toimisto", Categories.OFFICE_GOVERNMENT, None),  # Toimisto (offices)
        ("luontotupa", Categories.COMMUNITY_CENTRE, None),  # Luontotupa (nature huts keep the hut over info desks)
        (
            "matkailuneuvon",
            Categories.TOURISM_INFORMATION,
            {"information": "office"},
        ),  # Matkailuneuvonta (tourist info)
        ("matkailuinfo", Categories.TOURISM_INFORMATION, {"information": "office"}),  # Matkailuinfo (tourist info)
        ("toimipiste", Categories.OFFICE_GOVERNMENT, None),
        (
            "palvelupaikka",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Palvelupaikka (service points)  # Toimipiste (service points)
        ("toimipaikka", Categories.OFFICE_GOVERNMENT, None),  # Toimipaikka (offices)
        ("museo", Categories.MUSEUM, None),  # Museo (museums)
        ("asiakaspalvelu", Categories.OFFICE_GOVERNMENT, None),  # Asiakaspalvelu (customer service)
        ("perhekeskus", Categories.OFFICE_GOVERNMENT, None),
        ("perhetyö", Categories.SOCIAL_FACILITY, None),  # Perhetyö (family work)  # Perhekeskus (family centres)
        ("kirjaamo", Categories.OFFICE_GOVERNMENT, None),  # Kirjaamo (registries)
        ("perheoikeudelliset", Categories.OFFICE_GOVERNMENT, None),  # Perheoikeudelliset (family-law services)
        ("vapaa-aikatoimi", Categories.OFFICE_GOVERNMENT, None),  # Vapaa-aikatoimi (leisure administration)
        ("vapaa-aikakeskus", Categories.COMMUNITY_CENTRE, None),  # Vapaa-aikakeskus (leisure centres)
        (
            "kulttuuri- ja vapaa-aika",
            Categories.OFFICE_GOVERNMENT,
            None,
        ),  # Kunnan kulttuuri- ja vapaa-aika (municipal culture/leisure depts)
        ("maistraatti", Categories.OFFICE_GOVERNMENT, None),  # Maistraatti (magistrates)
        ("sivistys", Categories.OFFICE_GOVERNMENT, None),  # Sivistys (education admin)
        ("maaseutu", Categories.OFFICE_GOVERNMENT, None),  # Maaseutu (rural services)
        ("varhaiskasvatus", Categories.OFFICE_GOVERNMENT, None),  # Varhaiskasvatus (early-education admin)
        ("perusopetus", Categories.OFFICE_GOVERNMENT, None),  # Perusopetus (basic-education admin)
        ("verotoimisto", Categories.OFFICE_GOVERNMENT, None),  # Verotoimisto (tax offices)
        ("verovirasto", Categories.OFFICE_GOVERNMENT, None),  # Verovirasto (tax offices)
        ("työllisyys", Categories.OFFICE_GOVERNMENT, None),  # Työllisyys (employment services)
        ("työvoima", Categories.OFFICE_GOVERNMENT, None),  # Työvoima (labour services)
        ("rakennusvalvonta", Categories.OFFICE_GOVERNMENT, None),  # Rakennusvalvonta (building control)
        ("rakennusvalvonnan", Categories.OFFICE_GOVERNMENT, None),  # Rakennusvalvonnan (building control, genitive)
        ("maanmittauslaitos", Categories.OFFICE_GOVERNMENT, None),  # Maanmittauslaitos (land survey offices)
        ("metsäkeskus", Categories.OFFICE_GOVERNMENT, None),  # Metsäkeskus (forest centre)
        ("ulosotto", Categories.OFFICE_GOVERNMENT, None),
        ("kotihoito", Categories.SOCIAL_FACILITY, None),  # Kotihoito (home care, outranks lähipalvelualue below)
        ("tulli", Categories.OFFICE_GOVERNMENT, None),  # Tulli (customs offices)
        ("kuntoutusohjaus", Categories.SOCIAL_FACILITY, None),  # Kuntoutusohjaus (rehab guidance)
        ("ohjaus", Categories.OFFICE_GOVERNMENT, None),  # Ohjaus (guidance desks)
        ("neuvonta", Categories.OFFICE_GOVERNMENT, None),  # Neuvonta (advice services)
        ("lähipalvelu", Categories.OFFICE_GOVERNMENT, None),  # Lähipalvelu (local service points)
        ("ohjaamo", Categories.OFFICE_GOVERNMENT, None),  # Ohjaamo (guidance hubs)
        ("asiointipiste", Categories.OFFICE_GOVERNMENT, None),
        ("hyvinvointikioski", Categories.OFFICE_GOVERNMENT, None),  # Hyvinvointikioski (wellbeing kiosks)
        ("kioski", Categories.SHOP_KIOSK, None),  # Kioski (kiosks)  # Asiointipiste (service points)
        ("palvelupiste", Categories.OFFICE_GOVERNMENT, None),  # Palvelupiste (service points)
        ("serviceenhet", Categories.OFFICE_GOVERNMENT, None),  # Serviceenhet (service units in Swedish)
        ("palvelutori", Categories.OFFICE_GOVERNMENT, None),  # Palvelutori (service desks)
        ("navigaattori", Categories.OFFICE_GOVERNMENT, None),  # Navigaattori (guidance service desks)
        ("päivystyksen", Categories.CLINIC_URGENT, None),  # Päivystyksen (on-call duty, genitive)
        ("palvelukeskus", Categories.SOCIAL_FACILITY, None),  # Palvelukeskus (service centres)
        ("palvelutalo", Categories.NURSING_HOME, None),  # Palvelutalo (sheltered housing)
        ("seniori", Categories.SOCIAL_FACILITY, None),  # Seniori (senior centres, outranks info desks below)
        ("luustoinfo", Categories.OFFICE_GOVERNMENT, None),  # Luustoinfo (bone-health info desks)
        ("kansalaisinfo", Categories.OFFICE_GOVERNMENT, None),  # Kansalaisinfo (citizen info desks)
        ("info", Categories.TOURISM_INFORMATION, {"information": "office"}),  # Info (city information desks)
        ("visitor centre", Categories.TOURISM_INFORMATION, {"information": "visitor_centre"}),
        ("visitor center", Categories.TOURISM_INFORMATION, {"information": "visitor_centre"}),
        ("sosiaali", Categories.SOCIAL_FACILITY, None),  # Sosiaali (social services)
        ("vanhainkoti", Categories.NURSING_HOME, None),  # Vanhainkoti (elderly homes)
        ("hoivakoti", Categories.NURSING_HOME, None),  # Hoivakoti (care homes)
        ("hoiva", Categories.SOCIAL_FACILITY, None),  # Hoiva (care homes)  # Kotihoito (home care)
        ("työpaja", Categories.SOCIAL_FACILITY, {"social_facility": "workshop"}),  # Työpaja (workshops)
        ("innopaja", Categories.SOCIAL_FACILITY, {"social_facility": "workshop"}),  # Innopaja (innovation workshops)
        ("taitopaja", Categories.SOCIAL_FACILITY, {"social_facility": "workshop"}),  # Taitopaja (craft workshops)
        ("ikäihmisten päivätoiminta", Categories.SOCIAL_FACILITY, None),  # Day activities for elderly
        ("ikäihmis", Categories.NURSING_HOME, None),  # Ikäihmis (elderly-care homes)
        ("kehitysvamma", Categories.SOCIAL_FACILITY, None),  # Kehitysvamma (developmental-disability services)
        ("vammais", Categories.SOCIAL_FACILITY, None),  # Vammais (disability services)
        ("lyhytaikaishoito", Categories.NURSING_HOME, None),  # Lyhytaikaishoito (respite care)
        ("lyhytaikaishoidon", Categories.NURSING_HOME, None),  # Lyhytaikaishoidon (respite care, genitive)
        ("lyhytaikaisyksikkö", Categories.NURSING_HOME, None),  # Lyhytaikaisyksikkö (short-stay units)
        ("palvelut", Categories.OFFICE_GOVERNMENT, None),  # Palvelut (municipal service units)
        ("palvelukoti", Categories.NURSING_HOME, None),  # Palvelukoti (service homes)
        ("palveluasumi", Categories.NURSING_HOME, None),  # Palveluasuminen (24h service housing)
        ("palveluasunnot", Categories.NURSING_HOME, None),  # Palveluasunnot (service flats, plural)
        ("palvelukodit", Categories.NURSING_HOME, None),  # Palvelukodit (service homes, plural)
        ("palvelu", Categories.OFFICE_GOVERNMENT, None),  # Palvelu (service desks)
        ("turvakoti", Categories.SOCIAL_FACILITY, {"social_facility": "shelter"}),
        ("päivätoiminta", Categories.SOCIAL_FACILITY, None),  # Päivätoiminta (day activities)
        ("päiväaikainen", Categories.SOCIAL_FACILITY, None),  # Päiväaikainen toiminta (daytime activities)
        ("al-anon", Categories.COMMUNITY_CENTRE, None),  # Al-Anon (peer support)
        ("vertaistuki", Categories.COMMUNITY_CENTRE, None),  # Vertaistuki (peer support)
        ("lastensuojelu", Categories.SOCIAL_FACILITY, None),  # Lastensuojelu (child welfare)
        ("vertaisryhm", Categories.COMMUNITY_CENTRE, None),  # Vertaisryhmä (peer-support groups)
        ("sydänkerho", Categories.COMMUNITY_CENTRE, None),  # Sydänkerho (heart clubs)
        ("sydänosasto", Categories.CLINIC, None),  # Sydänosasto (cardiac wards)
        ("asumi", Categories.SOCIAL_FACILITY, None),  # Asumi (housing services)
        ("boende", Categories.SOCIAL_FACILITY, None),
        ("bostad", Categories.SOCIAL_FACILITY, None),  # Bostad (housing in Swedish)
        ("bostäder", Categories.SOCIAL_FACILITY, None),  # Bostäder (housing in Swedish, plural)
        ("hemmet", Categories.SOCIAL_FACILITY, None),  # Hemmet (housing in Swedish)  # Boende (housing in Swedish)
        ("kuntout", Categories.SOCIAL_FACILITY, None),  # Kuntout (rehabilitation)
        ("työterveys", Categories.CLINIC, None),  # Työterveys (occupational health)
        ("matonpesupaikka", Categories.CARPET_WASHING, None),
        (
            "matonpesu",
            Categories.CARPET_WASHING,
            None,
        ),  # Matonpesu (carpet washing)  # Matonpesupaikka (carpet washing)
        ("kierrätys", Categories.RECYCLING, None),  # Kierrätys (recycling)
        ("kiertopiste", Categories.RECYCLING, None),  # Kiertopiste (reuse points)
        ("jäteasema", Categories.RECYCLING, None),  # Jäteasema (waste stations)
        ("jätepiste", Categories.RECYCLING, None),  # Jätepiste (waste points)
        ("puutarhajäte", Categories.RECYCLING, None),  # Puutarhajäte (garden waste)
        ("hyötykäyttö", Categories.RECYCLING, None),  # Hyötykäyttö (reuse stations)
        ("hyödyksi", Categories.RECYCLING, None),  # Hyödyksi-asemat (reuse stations)
        ("hävikkiterminaali", Categories.SOCIAL_FACILITY, None),  # Hävikkiterminaali (surplus-food terminals)
        ("terminaali", Categories.FERRY_TERMINAL, None),  # Terminaali (ferry passenger terminals)
        ("vaateapu", Categories.SOCIAL_FACILITY, None),  # Vaateapu (clothing aid)
        ("tavara-apu", Categories.SOCIAL_FACILITY, None),  # Tavara-apu (goods aid)
        ("ruoka-apu", Categories.SOCIAL_FACILITY, None),  # Ruoka-apu (food aid)
        ("ruokajako", Categories.SOCIAL_FACILITY, None),  # Ruokajako (food distribution)
        ("hävikki", Categories.SOCIAL_FACILITY, None),  # Hävikki (surplus-food distribution)
        ("hautausmaa", None, {"landuse": "cemetery"}),  # Hautausmaa (cemeteries, incl. pet cemeteries)
        ("krematorio", None, {"amenity": "crematorium"}),  # Krematorio (crematoriums)
        ("kodat", Categories.SHELTER, None),  # Kodat (kota shelters, plural)
        ("varikko", None, {"amenity": "depot"}),  # Varikko (depots)
        ("lajitteluasema", Categories.RECYCLING, None),  # Lajitteluasema (sorting stations)
        ("lajittelupiha", Categories.RECYCLING, None),  # Lajittelupiha (sorting yards)
        ("kierrätyspiha", Categories.RECYCLING, None),  # Kierrätyspiha (recycling yards)
        ("siirtokuormausasema", Categories.RECYCLING, None),  # Siirtokuormausasema (transfer stations)
        ("kaatopaikka", None, {"landuse": "landfill"}),  # Kaatopaikka (dump sites, incl. snow dumps)
        ("lähiasema", Categories.CLINIC, None),  # Lähiasemat (local health stations)
        ("selviämis", Categories.CLINIC, None),  # Selviämisasemat (sobering-up stations)
        ("sydänasema", Categories.CLINIC, None),  # Sydänasema (acute cardiac unit)
        ("ensihoito", Categories.FIRE_STATION, None),  # Ensihoitoasemat (EMS stations)
        ("ekoasema", Categories.RECYCLING, None),  # Ekoasemat (eco recycling points)
        ("kohtaamisasema", Categories.COMMUNITY_CENTRE, None),  # Kohtaamisasemat (meeting points)
        ("miesten asema", Categories.COMMUNITY_CENTRE, None),  # Miesten asema (men's support points)
        ("businessasema", Categories.OFFICE_GOVERNMENT, None),  # BusinessAsema (business service point)
        ("puolustusasema", Categories.TOURISM_ATTRACTION, None),  # Puolustusasemat (war-history sites)
        ("kaavoitus", Categories.OFFICE_GOVERNMENT, None),  # Kaavoitus (planning offices)
        ("testausasema", None, None),  # Testausasemat (test stations): no precise filing, keep generic
        ("testiasema", None, None),  # Testiasemat (test stations): no precise filing, keep generic
        ("asema", None, {"railway": "station", "public_transport": "station"}),  # Asema (railway stations)
        ("vuokraamo", Categories.SHOP_RENTAL, None),
        ("kirpputori", Categories.SHOP_SECOND_HAND, None),  # Kirpputori (flea markets)
        ("kirppis", Categories.SHOP_SECOND_HAND, None),  # Kirppis (flea markets)  # Vuokraamo (rental shops)
        ("reshop", Categories.SHOP_SECOND_HAND, None),  # Reshop (second-hand shops)
        ("pysäköintialue", Categories.PARKING, None),
        ("viljelypalsta", Categories.ALLOTMENTS, None),  # Viljelypalsta (allotments)
        (
            "siirtolapuutarha",
            Categories.ALLOTMENTS,
            None,
        ),  # Siirtolapuutarha (allotments)  # Pysäköintialue (parking areas)
        ("lainaamo", Categories.TOOL_LIBRARY, None),  # Lainaamo (lending libraries)
        ("ulkoilualue", Categories.LEISURE_PARK, None),  # Ulkoilualue (outdoor areas)
        ("leirikeskus", Categories.TOURISM_CAMP_SITE, None),  # Leirikeskus (camp centres)
        ("leirialue", Categories.TOURISM_CAMP_SITE, None),  # Leirialue (camp areas)
        ("leiriytymispaikka", Categories.TOURISM_CAMP_SITE, None),  # Leiriytymispaikka (camping spots)
        ("ampumarata", None, {"leisure": "shooting_ground", "sport": "shooting"}),  # Ampumarata (shooting ranges)
        ("leirintäalue", Categories.TOURISM_CAMP_SITE, None),  # Leirintäalue (camping grounds)
        ("virkistysalue", Categories.LEISURE_PARK, None),  # Virkistysalue (recreation areas)
        ("laavu", Categories.SHELTER, None),
        (
            "kalastusalue",
            None,
            {"leisure": "fishing"},
        ),  # Kalastusalue (fishing areas; after laavu so area shelters keep shelter)
        ("hätämajoitus", Categories.SHELTER, None),  # Hätämajoitus (emergency housing)
        ("luontokeskus", Categories.MUSEUM, None),  # Luontokeskus (nature centres)  # Laavu (lean-to shelters)
        ("vessa", Categories.TOILETS, None),  # Vessa (toilets)
        ("talvipuutarha", None, {"leisure": "botanical_garden"}),  # Talvipuutarha (botanical garden)
        ("kasvitieteelli", None, {"leisure": "botanical_garden"}),  # Kasvitieteelliset puutarhat
        ("puisto", Categories.LEISURE_PARK, None),  # Puisto (parks)
        ("veistos", None, {"tourism": "artwork", "artwork_type": "sculpture"}),  # Veistos (sculptures; parks keep park)
        ("taideteos", Categories.TOURISM_ARTWORK, None),  # Taideteos (artworks)
        ("päiväkeskus", Categories.SOCIAL_FACILITY, None),  # Päiväkeskus (day centres)
        ("autiotupa", Categories.TOURISM_WILDERNESS_HUT, None),  # Autiotupa (wilderness huts)
        ("tupa", Categories.COMMUNITY_CENTRE, None),  # Tupa (meeting houses, compound-final)
        ("laituri", Categories.MAN_MADE_PIER, None),  # Laituri (piers)
        ("venepaikka", Categories.MARINA, None),  # Venepaikka (boat berths)  # Satama (harbours)
        ("vesipiste", Categories.DRINKING_WATER, None),  # Vesipiste (drinking-water points)
        ("vedenjakelu", Categories.DRINKING_WATER, None),  # Vedenjakelu (water distribution points)
        ("vesiposti", Categories.DRINKING_WATER, None),  # Vesiposti (municipal water posts)
        ("veneenlaskupaikka", Categories.LEISURE_SLIPWAY, None),  # Veneenlaskupaikka (boat launch ramps)
        (
            "lintutorni",
            Categories.TOURISM_VIEWPOINT,
            {"man_made": "tower", "tower:type": "observation"},
        ),  # Lintutorni (bird towers)
        ("lintulava", Categories.TOURISM_VIEWPOINT, None),  # Lintulava (birdwatching platforms)
        (
            "näköalatorni",
            Categories.TOURISM_VIEWPOINT,
            {"man_made": "tower", "tower:type": "observation"},
        ),  # Näköalatorni (observation towers)
        ("sairaanhoito", Categories.CLINIC, None),  # Sairaanhoito (nursing care)
        ("korvaushoito", Categories.CLINIC, None),  # Korvaushoito (substitution treatment)
        ("vieroitus", Categories.CLINIC, None),  # Vieroitus (detox units)
        ("leikkaus", Categories.CLINIC, None),  # Leikkaus (surgery units)
        ("anestesia", Categories.CLINIC, None),  # Anestesia (anaesthesia units)
        ("sisätauti", Categories.CLINIC, None),  # Sisätaudit (internal medicine)
        ("silmätauti", Categories.CLINIC, None),  # Silmätaudit (eye care)
        ("syöpätauti", Categories.CLINIC, None),  # Syöpätaudit (cancer care)
        ("sairaansija", Categories.CLINIC, None),  # Sairaansijat (hospital beds)
        ("tehohoito", Categories.CLINIC, None),  # Tehohoito (intensive care)
        ("munuais", Categories.CLINIC, None),  # Munuais- (renal units)
        ("tähystys", Categories.CLINIC, None),  # Tähystys (endoscopy units)
        ("dialyysi", Categories.CLINIC, None),  # Dialyysi (dialysis units)
        ("neulanvaihto", Categories.CLINIC, None),  # Neulanvaihto (needle-exchange points)
        ("tartuntatauti", Categories.CLINIC, None),  # Tartuntataudit (infectious diseases)
        ("hoitokoti", Categories.NURSING_HOME, None),  # Hoitokoti (care homes)
        ("hoitokodit", Categories.NURSING_HOME, None),  # Hoitokodit (care homes, plural)
        ("eläinhoitola", Categories.VETERINARY, None),  # Eläinhoitola (animal-care clinics)
        ("lintuhoitola", Categories.VETERINARY, None),  # Lintuhoitola (bird-care clinics)
        ("hoito", Categories.OFFICE_GOVERNMENT, None),  # Hoito (care service desks)
        (
            "väestönsuoja",
            Categories.MILITARY_BUNKER,
            {"bunker_type": "bomb_shelter"},
        ),  # Väestönsuoja (civil-defence shelters)
        ("yhteiskalliosuoja", Categories.MILITARY_BUNKER, {"bunker_type": "bomb_shelter"}),
    )
    # tori matches standalone and market compounds (kauppatori) but never
    # auditorio/laboratorio/toimisto, which do not end in tori.
    TORI_RE = re.compile(r"(?:\btori\b|\w+tori\b)")
    SAUNA_RE = re.compile(r"(?:\bsaunat?\b|\w+saunat?\b)")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ids: list[str] = []
        self._seen_pages: set[int] = set()
        # Bounded-window org join: channel items wait only for their own
        # org batch (one round-trip), never the whole crawl. Orgs are ~5k
        # nationally; the cache keeps each fetched once.
        self._org_names: dict[str, str] = {}
        self._seen_orgs: set[str] = set()
        self._pending: dict[str, list[Feature]] = {}
        venue_words = (
            {k for k, _, _ in self.CATEGORY_RULES}
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
            }
        )
        self.GENERIC_WORDS = {w.lower() for w in venue_words}
        self.FIXTURE_RE = re.compile("|".join(sorted(self.GENERIC_WORDS, key=len, reverse=True)))
        self._rules = []
        for k, cat, extra in self.CATEGORY_RULES:
            if k in ("lab", "kirkko", "kappeli", "seurakuntatalo", "halli", "tupa"):
                # Compound-end only: Tykslab/Fimlab, Aurejärven kirkko and
                # Säkylähalli match; labyrintti, Kirkkojärvi, Kirkkopuisto,
                # hallitus and maaseutupalvelut (tupa mid-compound) do not.
                rx = re.compile(r"\w*" + re.escape(k) + r"\b")
            elif k == "info":
                # Info desks read prefix or suffix (Infopiste, Pääinfo);
                # Sinfonia never matches.
                rx = re.compile(r"info\b|\binfo")
            elif k == "tulli":
                # Customs offices (Lentotulli) share the stem with
                # district/building names (Tullinkulma, Tullikamari,
                # Tullisaari, Tullinpuomi, Tullintori, Tullivuorentie):
                # those never match.
                rx = re.compile(r"tulli(?!nkulma|kamari|vuor|saar|npuomi|ntori)")
            elif k == "skola":
                # Askola the municipality is not a skola (school).
                rx = re.compile(r"(?<!a)skola")
            elif k == "koulu":
                # Koulutalo, koulukoti and koulun stay schools; koulutus
                # and its inflections (koulutuksen, koulutukset) plus
                # school-aged (kouluikäinen, kouluiässä) never match.
                rx = re.compile(r"\w*koulu(?!tus|tuk|ikä|iä)")
            elif k == "asema":
                # Station words, compound-final only: customer-service desks
                # at Helsinki-Vantaa ("...lentoasemalla") are offices, a bare
                # Lentoasema is no one's railway station, and inflected
                # station modifiers ("metroaseman väestönsuoja",
                # "terveysasemilla" services) must not file as stations.
                # Rautatieasema keeps its own earlier rule.
                rx = re.compile(r"(?<!lento)asema\b")
            else:
                rx = re.compile(re.escape(k))
            self._rules.append((rx, cat, extra))

    def _count(self, key: str, n: int = 1) -> None:
        crawler = getattr(self, "crawler", None)
        stats = crawler.stats if crawler else None
        if stats is None:
            return
        stats.inc_value(f"{self.name}/{key}", n)

    def list_url(self, page: int) -> str:
        return f"{self.api_base_url}/ServiceChannel/type/ServiceLocation?" + urlencode({"page": page})

    async def start(self):
        yield JsonRequest(url=self.list_url(1), cb_kwargs={"page": 1})

    def parse(self, response: TextResponse, page: int):
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("page/bad_json")
            self.logger.error("bad JSON from %s", response.url)
            return
        if not isinstance(payload, dict):
            self._count("page/bad_shape")
            return
        self._seen_pages.add(page)
        known_ids = set(self._ids)
        for row in payload.get("itemList") or []:
            if isinstance(row, dict) and row.get("id"):
                self._ids.append(str(row["id"]))
        self._count("list/ids", len(payload.get("itemList") or []))
        total = payload.get("pageCount")
        if isinstance(total, int) and page < total and page + 1 not in self._seen_pages:
            yield JsonRequest(url=self.list_url(page + 1), cb_kwargs={"page": page + 1})
            return
        if not isinstance(total, int) and payload.get("itemList"):
            # Server ignoring ?page would loop forever on page 1's shape.
            if page + 1 not in self._seen_pages and set(self._ids) > known_ids:
                yield JsonRequest(url=self.list_url(page + 1), cb_kwargs={"page": page + 1})
                return
        yield from self._batch_requests()

    def _batch_requests(self) -> Iterable[JsonRequest]:
        # Detail endpoint takes comma-joined guids (repeated ?guids= params
        # return only the first); batch_size keeps URLs short (see above).
        for i in range(0, len(self._ids), self.batch_size):
            chunk = self._ids[i : i + self.batch_size]
            yield JsonRequest(
                url=f"{self.api_base_url}/ServiceChannel/list?" + urlencode({"guids": ",".join(chunk)}),
                callback=self.parse_batch,
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

    def _apply_operator(self, item: Feature, org_name: str | None) -> None:
        if item.get("operator"):
            # Branch-agency suffixes ("/Kela") already named the provider.
            self._count("operator/branch_agency_kept")
            return
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
        # Department suffixes name the desk, not the operator
        # ("Helsingin kaupunki, Kasvatuksen ja koulutuksen toimiala").
        # Brand suffixes name the marketing brand, not the operator
        # ("Pohjois-Karjalan hyvinvointialue – Siun sote"); legal
        # association tails ("FinFami - Uusimaa ry") and Swedish parallels
        # stay, short marker-less tails strip.
        operator = org_name.split(",", 1)[0].strip() or org_name
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
        if qid := self.OPERATORS_WIKIDATA.get(operator):
            item["operator_wikidata"] = qid
        else:
            self._count("operator/no_qid")
        is_company = bool(re.search(r"\b(oy|ab)\.?$", operator, flags=re.IGNORECASE))
        private_org = self._is_private_org(operator) or self._is_private_org(org_name.split(",", 1)[0].strip())
        if is_company or private_org:
            # Companies and associations delivering public services are
            # private operators (user ruling extends the Oy/Ab precedent).
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
        if private_org and not is_company and self._tag(item, "office") == "government":
            # Association-run desks are association offices, not government
            # ones (office lives in extras; a top-level write would raise).
            self._count("operator/office_demoted")
            item["extras"]["office"] = "association"

    def parse_batch(self, response: TextResponse):
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("page/bad_json")
            return
        if not isinstance(payload, list):
            self._count("page/bad_shape")
            return
        fresh_orgs: list[str] = []
        for channel in payload:
            if not isinstance(channel, dict):
                continue
            if item := self.parse_channel(channel):
                org_id = channel.get("organizationId")
                if not org_id:
                    self._apply_operator(item, None)
                    yield item
                elif org_id in self._org_names:
                    self._apply_operator(item, self._org_names[org_id])
                    yield item
                else:
                    self._pending.setdefault(str(org_id), []).append(item)
                    if str(org_id) not in self._seen_orgs:
                        self._seen_orgs.add(str(org_id))
                        fresh_orgs.append(str(org_id))
        for i in range(0, len(fresh_orgs), self.batch_size):
            chunk = fresh_orgs[i : i + self.batch_size]
            yield JsonRequest(
                url=f"{self.api_base_url}/Organization/list?" + urlencode({"guids": ",".join(chunk)}),
                callback=self.parse_orgs,
                errback=self.errback_orgs,
            )

    def parse_orgs(self, response: TextResponse):
        try:
            payload = response.json()  # ty: ignore[unresolved-attribute]
        except ValueError:
            self._count("org/bad_json")
            yield from self._flush_request_orgs(getattr(response, "url", "") or "")
            return
        if not isinstance(payload, list):
            self._count("org/bad_shape")
            yield from self._flush_request_orgs(getattr(response, "url", "") or "")
            return
        for org in payload:
            if not isinstance(org, dict) or not org.get("id"):
                continue
            name = self._lang_value(org.get("organizationNames") or [], "fi", "sv", "en")
            self._org_names[str(org["id"])] = name or ""
            for item in self._pending.pop(str(org["id"]), []):
                self._apply_operator(item, name)
                yield item

    def _flush_request_orgs(self, url: str) -> Iterable[Feature]:
        # Flush the window without operators rather than losing it: recover
        # the org ids from the failed request URL (cf. s-market errback).
        match = re.search(r"guids=([^&]*)", url or "")
        for org_id in (unquote(match.group(1)).split(",") if match else []):
            for item in self._pending.pop(org_id, []):
                self._apply_operator(item, None)
                yield item

    def errback_orgs(self, failure) -> Iterable[Feature]:
        # Flush the window without operators rather than losing it: recover
        # the org ids from the failed request URL (cf. s-market errback).
        request = getattr(failure, "request", None)
        url = getattr(request, "url", "") or ""
        self._count("org/failed")
        yield from self._flush_request_orgs(url)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        from scrapy import signals

        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider) -> None:
        leftover = {org_id: len(items) for org_id, items in self._pending.items() if items}
        if leftover:
            self._count("org/unflushed_on_close", sum(leftover.values()))
            self.logger.error("ptv_fi: unflushed org windows on close: %d orgs", len(leftover))

    # Contact-details placeholders filed as names ("Kontaktuppgifter"
    # with no Finnish name): never POI names, fall back to real ones.
    NAME_PLACEHOLDERS = frozenset({"kontaktuppgifter"})

    def _names(self, channel: dict) -> dict[str, str]:
        # The official Name wins over AlternativeName ("Talaskankaan
        # retkeilyreitti", not "Talaskangas"); displayNameType breaks
        # ties, first-listed wins otherwise. Single-name records behave
        # exactly as before.
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
        for lang, variants in by_lang.items():
            picked = None
            for dtype, dlang in display:
                if dlang == lang:
                    picked = next((v for t, v in variants if t == dtype), None)
                    break
            if picked is None:
                picked = next((v for t, v in variants if t == "Name"), variants[0][1])
            out[lang] = picked
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
            or "lenkki" in lowered
            or "juoksu" in lowered
            or "latu" in lowered
            or "ladut" in lowered
            or "polut" in lowered
            or "reitti" in lowered
            or "reitit" in lowered
            or "reitistö" in lowered
            or self.KM_RE.search(lowered)
        ):
            # Tracks, loop trails and distance-marked routes are linear, not places.
            return "non_place/track"
        return None

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

    def _coords(self, street: dict) -> tuple[float, float] | None:
        # Fields are named latitude/longitude but hold TM35FIN
        # northing/easting; convert to WGS84 lon/lat. NotReceived/Failed
        # states (6 + 2 in the detail sample) mark placeholder coords.
        if (street.get("coordinateState") or "") in ("NotReceived", "Failed"):
            self._count("coords/dropped_state")
            return None
        try:
            northing = float(str(street.get("latitude")).strip())
            easting = float(str(street.get("longitude")).strip())
        except (TypeError, ValueError, AttributeError):
            return None
        try:
            lon, lat = self._transformer.transform(easting, northing)
        except ValueError:
            return None
        if not (59.0 <= lat <= 71.0 and 19.0 <= lon <= 32.0):
            return None
        self._count("coords/" + str((street.get("coordinateState") or "missing")))
        return lon, lat

    # Tails naming institutions are venues; the facility names the POI
    # ("Laihian Keskuskoulu / Yläkoulun yksikkö"). Narrower than the
    # service-map list on purpose: PTV shapes are org-branch offices.
    INSTITUTION_TAILS = (
        "koulu",
        "lukio",
        "yläaste",
        "ala-aste",
        "sairaala",
        "kirjasto",
        "museo",
        "teatteri",
        "kirkko",
        "kappeli",
        "päiväkoti",
        "opisto",
        "uimahalli",
        "terveysasema",
        "neuvola",
        "virasto",
        "hammashoitola",
        "poliklinikka",
        "skolan",
    )
    # Branch-office designators name the org's local desk, not a venue
    # ("Pohjanmaan elinvoimakeskus, Kokkolan toimipaikka"): keep the head.
    BRANCH_TAILS = ("toimipiste", "toimipaikka", "toimisto")
    # Hosted school units: the unit is the POI, the school the venue
    # ("Kellon koulu, Kiviniemen yksikkö").
    UNIT_TAILS = ("yksikkö", "opetuspiste", "ryhmäkoti")
    # Service areas and category-descriptors are designations, never venues.
    AREA_TAILS = ("lähipalvelualue", "palvelualue", "toiminta-alue", "ulkoilusaari")

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
        return re.search(r"(^|\s)alue$", lowered) is not None and not lowered.endswith(("ulkoilualue", "virkistysalue"))

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
    ROOM_WORDS = (
        "sali",
        "kenttä",
        "halli",
        "allas",
        "rata",
        "tila",
        "huone",
        "koppi",
        "katos",
        "kota",
        "laavu",
        "grillipaikka",
        "heittopaikka",
        "huoltorakennus",
        "ulkokuntoilupaikka",
    )
    # Single memorial objects never split (title + designation of one artwork).
    MEMORIAL_WORDS = ("muistomerkki", "monumentti", "patsas", "memorial")
    # Service heads hosted at schools: the service names the POI, the
    # school is the venue ("Opiskeluhuolto, Karhusuon koulu", cf. the
    # service-map comma-venue rule). Slash pairs already resolve this way.
    SERVICE_HEADS = ("opiskeluhuolto", "kouluterveydenhuolto", "opiskeluterveydenhuolto")
    # Generic service words heading "<service>, <unit>" names
    # ("Kuvantaminen, Pirkkala Pirkkalan röntgen"; "Fysiatrian
    # poliklinikka, Vaasa", the county's Vaasa branch): the service names
    # the POI, the remainder the branch.
    BRANCH_HEADS = ("kuvantaminen", "laboratorio", "näytteenotto", "poliklinikka")
    # Service/unit nouns for host<>facility inversion, both directions
    # ("Lasten puheterapia, Perhekeskus Pohjatuuli" and its mirror).
    SERVICE_TAILS = (
        "yksikkö",
        "ryhmäkoti",
        "lastenkoti",
        "opetuspiste",
        "neuvola",
        "terapia",
        "poliklinikka",
        "hammashoitola",
        "kuntoutus",
        "rokotus",
        "vastaanotto",
        "ravintola",
        "keittiö",
        "kahvila",
        "kioski",
        "kauppa",
        "apteekki",
        "neuvonta",
        "ohjaus",
        "palvelu",
        "opastus",
        "päivätoiminta",
        "kalastuspaikka",
        "opiskeluhuolto",
        "kouluterveydenhuolto",
        "opiskeluterveydenhuolto",
    )
    # Hospital acronyms name venues, never services (", Tyks"; "OYSin ...").
    HOSPITAL_ACRONYMS = frozenset({"TYKS", "OYS", "HUS", "TAYS", "KYS"})
    # Bare acronym units at hospital heads ("Vatsakeskus, Tays Hatanpää")
    # are hospital departments: unit words licensing the clinic filing.
    ACRONYM_UNIT_WORDS = ("keskus", "yksikkö", "osasto", "klinikka", "poliklinikka", "vastaanotto")
    # Swedish institution words for bilingual dash names (cf. Eskola: the
    # boundary keeps Finnish Eskola/places whole).
    SWEDISH_WORD_RE = re.compile(r"\b(apotek(et)?|skola(n)?|daghem(met)?|bibliotek(et)?)", re.IGNORECASE)
    # Branch-of-agency suffixes name the service provider, never the POI
    # ("Kokemäen Asiointipiste/Kela" is the city's desk serving Kela).
    AGENCY_SUFFIX_RE = re.compile(r"/\s*kela\b(?=,|\s*$)", re.IGNORECASE)
    # Station-village post offices file under their municipality
    # ("ORIVESI AS" -> "Orivesi").
    STATION_SUFFIX_RE = re.compile(r"\s+as$", re.IGNORECASE)
    # Tails naming a school building (narrower than the category table:
    # venue evidence, not filing).
    SCHOOL_TAIL_RE = re.compile(
        r"(koulu|lukio|opisto|päiväkoti|esiopetus|yläaste|ala-aste|skola|daghem|högstadium|lågstadium)"
    )
    # Comma tails that are street addresses (cf. service-map COMMA_STREET_RE).
    COMMA_STREET_RE = re.compile(
        r"(tie|katu|kuja|polku|väylä|raitti|ranta|kaari|esplanadi|bulevardi|vägen|väg|gatan|gata|gränden|gränd|stigen|stig)\s+\d"
    )

    def _is_institution(self, text: str) -> bool:
        return re.search(r"\w*(?:" + "|".join(self.INSTITUTION_TAILS) + r")$", text) is not None

    def _clean_name(self, raw: str) -> str:
        # Bureau tails are record metadata, not name parts (cf. service-map
        # unit 79871: bureau tails stripped the same way). A dangling
        # trailing comma (data-entry cut-off) strips first so boilerplate
        # patterns match ("... järjestämispaikka,").
        primary = re.sub(r",\s*$", "", raw.replace("\u00a0", " ").strip()).strip()
        # Stray spaces before commas are feed dirt ("Prästgårdsbackens
        # förskola , Gesterby"): collapse so comma patterns match.
        primary = re.sub(r"\s+,", ",", primary).strip()
        # PTV quality-rating artifacts ("Liina päivätoiminta 2*"): the
        # star drops, the number stays.
        primary = re.sub(r"\s*(\d+)\*\s*$", r" \1", primary).strip()
        # Trailing coordinate tails are location metadata, not name parts
        # ("Mustasaari, P 60° 10,343' ja I 24° 52,123'").
        primary = re.sub(r",?\s*(?:[PN]\s*)?\d+\s*°.*$", "", primary).strip()
        primary = re.sub(r",\s*Kasvatuksen ja koulutuksen.*$", "", primary).strip()
        primary = re.sub(r",\s*Sektorn för fostran och utbildning.*$", "", primary).strip()
        primary = re.sub(r",\s*Education Division.*$", "", primary).strip()
        primary = self.AGENCY_SUFFIX_RE.sub("", primary).strip()
        before_boilerplate = primary
        primary = re.sub(r"\s*-palvelun järjestämispaikka\s*(?:,\s*\d+)?\s*$", "", primary).strip()
        # A stripped suffix leaves the service's own name as-is ("Näe hyvä
        # mussa -leirit lapsille"): the remainder names the service, so
        # lowercase-dash descriptors never strip below.
        boilerplate_stripped = primary != before_boilerplate
        primary = re.sub(r",\s*palvelupaikka\s*$", "", primary).strip()
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
            self._count("operator/branch_agency")
            item["operator"] = agency
        if self._tag(item, "amenity") in ("school", "college", "kindergarten"):
            # branch=* is chain retail, not schools: campus qualifiers
            # stay in the name, never split off (cf. Stadin ammattiopisto).
            return
        if (
            "," in signed
            and (
                any(shown.lower().endswith(word) for word in self.BRANCH_HEADS)
                or any(
                    signed.split(",")[0].strip().lower() == word
                    or signed.split(",")[0].strip().lower().startswith(word + " ")
                    for word in self.BRANCH_HEADS
                )
            )
            and not signed.split(",")[0].strip().endswith("-")
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
                and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", tail)
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
        branch = item.get("branch")
        if branch and (shown or "").casefold() == branch.casefold():
            # A branch repeating the name word for word ("Poliklinikka")
            # is not a branch.
            self._count("name/branch_dup_name")
            del item["branch"]
        branch = item.get("branch")
        if branch and city_src and branch.casefold() == city_src.strip().casefold():
            # A branch repeating the municipality ("Ivalo") is not a
            # branch; the city field carries it.
            self._count("name/branch_dup_city")
            del item["branch"]

    # Company/association markers for operator detection. Dotted forms
    # (r.y./r.f.) consume the trailing dot without a boundary (Derby
    # still stays whole via the leading boundary). Ay (avoin yhtiö) and
    # öb (Swedish öppet bolag, often truncated to Ö.) mark partnerships.
    OPERATOR_END_RE = (
        r"(\b(oy|ab|ry|r\.y\.?|r\.f\.?|tmi|toiminimi|ky|ay|öb|ö\.b?\.?|säätiö|sr)|(yhdistys|förening|seurakunta))\.?$"
    )
    # Bare-name private operators without a marker (Red Cross districts,
    # settlement houses, Attendo care homes, säätiö foundations).
    PRIVATE_SUBSTRINGS = ("punainen risti", "setlementti", "attendo", "säätiö", "sininauha")

    def _post_city(self, office: str | None) -> str | None:
        if not office or not office.strip():
            return None
        return self.STATION_SUFFIX_RE.sub("", office.strip())

    def _municipality_name(self, street: dict, channel: dict) -> str | None:
        # Visit-point municipality first; channel service areas only when
        # they agree on a single municipality (169 multi-municipality
        # channels stay ambiguous and fall back to the post office).
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
                if name and name.strip() and name.strip() not in seen:
                    seen.append(name.strip())
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

    def _has_operator_word(self, text: str) -> bool:
        # Short forms need word boundaries (Derby stays whole); yhdistys
        # and förening match inside compounds (kannatusyhdistys). A leading
        # Tmi marks toiminimi operators ("Tmi Petri Lehto").
        stripped = text.strip()
        return (
            re.search(r"^tmi\b", stripped, flags=re.IGNORECASE) is not None
            or re.search(self.OPERATOR_END_RE, stripped, flags=re.IGNORECASE) is not None
        )

    def _is_private_org(self, operator: str) -> bool:
        # Companies and associations delivering public services, whether
        # marked (Oy, ry, Tmi, kassa, säätiö, seura/kerho societies, ay/öb
        # partnerships, RIKU, mid-string "ry") or known bare names (Red
        # Cross, Setlementti, Attendo). Parishes (seurakunta) are
        # public-law bodies, never private, unless carrying a
        # company/association marker themselves
        # ("X seurakunta ry" stays private).
        lowered = operator.lower()
        if "seurakunta" in lowered and not re.search(r"\b(oy|ab|ry|r\.y\.?|tmi|toiminimi)\b", lowered):
            return False
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
    def _tag(item: Feature, key: str):
        # Category tags land in extras (Feature rejects them top-level);
        # read the level that carries them.
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
        if not re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+(?: [A-ZÅÄÖ][a-zåäö-]+){1,2}", text.strip()):
            return False
        return not self._has_fixture(text)

    def _is_proper_tail(self, text: str) -> bool:
        # A non-initial capitalized tail token outside the generic
        # vocabulary names a distinctive unit ("Sipoon Enter"); leading
        # place names ("Pöytätennisalue", "Hiekkakenttä") never match.
        if self._is_operator_shaped(text):
            return False
        tokens = [t for t in re.split(r"[\s,./():-]+", text) if t]
        for token in tokens[1:]:
            if re.match(r"[A-ZÅÄÖ]", token) and token.lower() not in self.GENERIC_WORDS:
                return True
        return False

    def _clean_located(self, located: str) -> str | None:
        # Operator tails, trailing cities and person names are not venues.
        if located.strip().casefold() in ("infopiste", "info"):
            # Bare info points are sub-facilities, never host venues.
            self._count("name/generic_venue_dropped")
            return None
        loc = re.sub(
            r"\s+\S*?(?:\b(?:oy|ab|ry|r\.y\.?|r\.f\.?|tmi|toiminimi|ky|ay|öb|ö\.b?\.?|säätiö)|(?:yhdistys|förening|seurakunta))\.?$",
            "",
            located.strip(),
            flags=re.IGNORECASE,
        ).strip(" ,")
        if loc != located.strip():
            self._count("name/operator_tail_stripped")
        if not loc:
            return None
        if re.search(r"(toiminta|toimintaa|toimintaan)$", loc.lower()) and not self._has_fixture(loc):
            # Bare activity descriptors are services, not venues
            # ("Allas - Tantsut / Ite ja yhessä - toiminta").
            self._count("name/activity_tail_dropped")
            return None
        if "," in loc:
            pre, _, city = loc.rpartition(",")
            if (
                pre.strip()
                and self._has_fixture(pre)
                and not self._has_fixture(city)
                and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", city.strip())
            ):
                self._count("name/city_tail_stripped")
                loc = pre.strip()
        if not loc:
            return None
        if self._is_person(loc):
            self._count("name/person_dropped")
            return None
        return loc

    def _room_tail(self, tail: str) -> bool:
        return any(word in tail.lower() for word in self.ROOM_WORDS)

    def _resolve_slash_room(
        self, head: str, tail: str, name: str, tag: str
    ) -> tuple[str, str | None, str | None] | None:
        # Rooms/fields are the facility, the host the venue
        # ("Santahaminan ala-asteen koulu / Koripallokenttä").
        # Self-named pairs ("... ulkokuntosali / Ulkokuntosali")
        # stay whole instead. Returns None when the tail is no room.
        if not self._room_tail(tail):
            return None
        if head.lower().endswith(tail.lower()):
            self._count("name/slash_self_kept")
            return name, None, None
        if re.search(r"\d", tail):
            self._count("name/slash_numbered_room")
            return tail, self._clean_located(head) or head, name
        self._count(tag)
        return tail, self._clean_located(head) or head, name

    def _resolve_slash_institution(self, head: str, tail: str, name: str) -> tuple[str, str | None, str | None] | None:
        # Institution-headed pairs: hosted units, rooms and exercise
        # grounds name the POI, the institution the venue.
        if not (self._is_institution(head.lower()) and not self._is_institution(tail.lower())):
            return None
        if any(word in tail.lower() for word in (*self.UNIT_TAILS, "toimipiste", "toimipaikka")):
            # Administrative units hosted at institutions
            # ("Laihian Keskuskoulu / Yläkoulun yksikkö").
            self._count("name/slash_facility")
            return tail, self._clean_located(head), name
        if (room := self._resolve_slash_room(head, tail, name, "name/slash_room")) is not None:
            return room
        if "lähiliikuntapaikka" in tail.lower():
            # Exercise grounds hosted at institutions ("Vuoniityn
            # peruskoulu / Lähiliikuntapaikka"): the ground names
            # the POI, the school the venue (cf. slash_room). Lives
            # here for Finnish institution heads; Swedish skol heads
            # resolve in _resolve_slash_pair below.
            self._count("name/slash_exercise_ground")
            return tail, self._clean_located(head), name
        return None

    def _resolve_slash_pair(self, head: str, tail: str, name: str) -> tuple[str, str | None, str | None] | None:
        # Institution, service, place and person tails resolve against the
        # head; returns None to fall through to room/appositive handling.
        if self._is_street_head(head):
            # Streets and street addresses are never venues
            # ("Kurkisuontie 2 / Hiekkakenttä"): the facility names
            # the POI, the address line carries the street.
            self._count("name/slash_street_head")
            return tail, None, name
        if re.search(r"(rakennus|talo)\s*\d", tail.lower()):
            # Numbered buildings qualify the head facility ("Eläintarhan
            # urheilukenttä / Huoltorakennus 4"): neither venues nor POIs.
            self._count("name/slash_building_kept")
            return head, None, name
        if (inst := self._resolve_slash_institution(head, tail, name)) is not None:
            return inst
        if "lähiliikuntapaikka" in tail.lower() and re.search(r"(koulu|skol)\w*", head.lower()):
            # Exercise grounds at schools, Finnish or Swedish
            # ("Vuoniityn peruskoulu / ...", "Åshöjdens grundskola /
            # Lähiliikuntapaikka"): the ground names the POI, the
            # school the venue (cf. slash_room; skol covers
            # skola/skolan, which institution tails lack).
            self._count("name/slash_exercise_ground")
            return tail, self._clean_located(head), name
        tail_base = tail.split(",")[0].strip()
        if self._is_bare_area(tail_base):
            # Bare coverage areas are not venues ("X / Tikkurilan alue"):
            # the signed form stays whole, never split into located_in.
            self._count("name/slash_area_kept")
            return name, None, None
        if self._is_unit_tail(tail_base) and not self._is_institution(head.lower()):
            # Unit qualifiers of a service without a host venue
            # ("Fysioterapia / Himangan yksikkö") name one service:
            # keep whole (cf. Stadin).
            self._count("name/slash_unit_kept")
            return name, None, None
        if any(word in tail_base.lower() for word in self.SERVICE_TAILS) and not self._is_institution(head.lower()):
            # Service-tailed pairs name the service ("Perhekeskus /
            # Neuvola", "Salmen ulkoilualue / Kalastuspaikka"); the venue
            # hosts it. Precedes the institution rule: a neuvola tail is
            # always the specific unit. Substring (not end-anchored) so
            # plural service desks ("ruokapalvelut") resolve too.
            self._count("name/slash_service_unit")
            return tail, self._clean_located(head) or head, name
        if self._is_institution(tail_base.lower()):
            # Named institutions as tails are venues
            # ("Iltapäivätoiminta / Steiner-koulu"); comma descriptors
            # ride along ("... / Kulosaaren ala-aste, Liikkis").
            self._count("name/slash_institution_venue")
            return head, self._clean_located(tail_base) or tail_base, name
        if self._has_fixture(tail) and re.search(r"(stadion|areena|keskus|puisto)$", head.lower()):
            # Place-headed pairs name the facility ("Uimastadion /
            # Pöytätennisalue"): the sub-area is the POI, the grounds
            # the venue. Precedes the district guess: stadiums end in
            # -n without being districts.
            self._count("name/slash_place_facility")
            return tail, self._clean_located(head) or head, name
        if re.fullmatch(r"[A-ZÅÄÖ][a-zåäöA-ZÅÄÖ-]+n", head) and " " not in head and self._has_fixture(tail):
            # Bare genitive-district head ("Pohjois-Espoon /
            # Niipperin matonpesupaikka"): the facility is the name.
            self._count("name/slash_district_facility")
            return tail, None, name
        if self._is_person(tail):
            # Contact persons are not venues ("Sari Wicklund"); host-named
            # units share a token with their school ("Sipoon Enter").
            head_tokens = {t.lower() for t in re.split(r"[\s,./():-]+", head) if len(t or "") >= 4}
            tail_tokens = {t.lower() for t in re.split(r"[\s,./():-]+", tail) if len(t or "") >= 4}
            if not (head_tokens & tail_tokens):
                self._count("name/person_dropped")
                return head, None, name
        if re.search(r"(toimisto|toimipiste|toimipaikka|virasto)$", head.lower()) and re.search(
            r"(toimipiste|toimipaikka)", tail.lower()
        ):
            # Office desks at office heads ("Keurusselän ...toimisto /
            # Mänttä-Vilppulan toimipiste"): the qualifier belongs in
            # the name (Stadin rule for offices).
            self._count("name/slash_office_kept")
            return name, None, None
        if (
            any(word in head.lower() for word in self.SERVICE_TAILS)
            and not self._is_institution(head.lower())
            and self._is_proper_tail(tail)
        ):
            # Services at proper-named venues ("Iltapäivätoiminta /
            # Leikkipuisto Nurkka"): the service names the POI, the
            # venue hosts it.
            self._count("name/slash_service_proper")
            return head, self._clean_located(tail) or tail, name
        if self._is_proper_tail(tail):
            self._count("name/slash_proper_facility")
            return tail, self._clean_located(head), name
        if (room := self._resolve_slash_room(head, tail, name, "name/slash_generic_room")) is not None:
            return room
        return None

    def _peel_slash(self, segments: list[str]) -> tuple[str, str | None] | None:
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
                or any(word in lowered for word in self.AREA_TAILS)
                or self._is_memorial(tail)
            ):
                self._count("name/slash_descriptor_dropped")
                segs.pop()
                continue
            break
        if not segs:
            return None
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
            r"(\b(?:oy|ab|ry|r\.y\.|r\.f\.)\b|(?:yhdistys|förening))", venue_org, flags=re.IGNORECASE
        ):
            self._count("name/slash_venue_org_stripped")
            return venue_head.strip()
        return tail

    def _split_slash(self, name: str) -> tuple[str, str | None, str | None] | None:
        # Spaced slash chains: peel descriptors, then resolve the pair.
        if " / " not in name:
            return None
        segments = [s.strip() for s in name.split(" / ")]
        # Parenthesised street address inside the last venue
        # ("Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)").
        tail = segments[-1]
        venue = re.sub(r"\s*\([^()]*\)$", "", tail).strip()
        if venue != tail and venue and self.COMMA_STREET_RE.search(tail.lower()):
            self._count("name/slash_paren_address")
            return venue, None, name
        if len(segments) >= 2 and self._island_area(segments[-1]):
            # Island service areas locate the POI ("Kahvila /
            # Ulkoilusaari") instead of peeling the island away.
            self._count("name/slash_area_island")
            return " / ".join(segments[:-1]), segments[-1], name
        if (
            len(segments) == 2
            and re.search(r"\w*(saari|luoto)$", segments[0].strip().lower())
            and self._has_fixture(segments[1])
        ):
            # Island-headed facility pairs ("Kaunissaari / Telttailu- ja
            # leiriytymispaikka 2."): the facility names the POI instead.
            self._count("name/slash_island_venue")
            return segments[1].strip(), segments[0].strip(), name
        if (
            len(segments) == 2
            and re.search(r"\w+lahti$", segments[0].strip().lower())
            and self._has_fixture(segments[1])
        ):
            # Bay-headed facility pairs ("Töölönlahti /
            # WDC-ulkokuntoilupaikka 1", "Tahvonlahti / Hiekkakenttä"):
            # the facility names the POI, the bay locates it. Compound
            # heads only, so the city of Lahti never matches.
            self._count("name/slash_bay_venue")
            return segments[1].strip(), segments[0].strip(), name
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
        peeled = self._peel_slash(segments)
        if peeled is None:
            return None
        head, tail = peeled
        if tail is None:
            return (head, None, name)
        tail = self._strip_venue_org(tail)
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
        return head, self._clean_located(tail), name

    def _resolve_nested(
        self, shown: str, located: str | None, official: str | None, name: str
    ) -> tuple[str, str | None, str | None]:
        # Nested remainder ("Talin puttirata / Mini-Tali" naming a practice
        # area): resolve the inner pair for the name, preferring its venue.
        inner = self._split_slash(shown)
        if inner is not None and " / " not in inner[0]:
            self._count("name/slash_nested")
            return inner[0], inner[1] or located, official or name
        return shown, located, official

    def _split_machine(self, name: str) -> tuple[str, str | None, str | None] | None:
        # Ticket/vending machines carry address + payment metadata after
        # commas ("Pysäköintilippuautomaatti 222, Pengerkatu 23,
        # korttimaksu"): the machine + id names the POI, the rest survives
        # in official_name. Runs before the slash dispatch so embedded
        # slashes in the location note never mis-split.
        if "automaatti" not in name.lower() or "," not in name:
            return None
        head = name.split(",")[0].strip()
        if not head or "automaatti" not in head.lower():
            return None
        self._count("name/comma_machine")
        return head, None, name

    def _split_paren(self, name: str, city: str | None) -> tuple[str, str | None, str | None] | None:
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
        if self._is_memorial(base, inner):
            self._count("name/paren_memorial")
            return name, None, None
        if "/" in base and base.count("/") == 1 and self.COMMA_STREET_RE.search(inner.lower()):
            # A real venue name with a parenthesised address beats an
            # operator-shaped head ("Pilke päiväkodit Oy/
            # Musiikkipäiväkoti Sinikello (Tuureporinkatu 5 E)").
            bhead, _, btail = base.rpartition("/")
            if btail.strip() and self._is_operator_shaped(bhead.strip()):
                self._count("name/slash_paren_address")
                return btail.strip(), None, name
        if " / " in base and any(word in base.rsplit(" / ", 1)[1].strip().lower() for word in self.ROOM_WORDS):
            # Facility tails with parenthesised qualifiers ("...
            # / Ulkokuntoilupaikka (Keski)"): the slash dispatch names
            # the tailed facility, parens included — paren handling
            # would keep whole or strand the qualifier as the venue.
            return None
        if not re.search(r"\d", inner) and self._has_fixture(inner):
            # Venue in parens ("... (Oltermannikeskus)").
            self._count("name/paren_venue")
            return base, inner, name
        if (
            self.COMMA_STREET_RE.search(inner.lower())
            or (re.search(r"\d", inner) and "," in inner)
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
            return sub[0], sub[1], name
        if re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", inner):
            # Single localities ("Totto-Halli (Muurola)") strip only when
            # they repeat known address context; village tails stay unless
            # they equal the municipality ("... (Idänpää)", Hämeenlinna).
            if city and inner.casefold() != city.strip().casefold():
                self._count("name/paren_village_kept")
                return name, None, None
            sub = self._split_name(base, city)
            self._count("name/paren_stripped")
            return sub[0], sub[1], name
        if "," in inner and all(re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", seg.strip()) for seg in inner.split(",")):
            # Proper-name venue lists ("...(Masto, Styyrpuuri,Vantti)"):
            # the units locate the POI. Coverage cities stay whole, as do
            # lists on names without facility evidence.
            listed = ", ".join(seg.strip() for seg in inner.split(","))
            if not (city and any(s.strip().casefold() == city.strip().casefold() for s in inner.split(","))) and (
                self._has_fixture(base) or self._category(base)[0] is not None
            ):
                self._count("name/paren_venue_list")
                return base, listed, name
        # Short qualifiers (target groups, levels, "(ulko)") are part of
        # the signed service name and stay whole.
        self._count("name/paren_qualifier_kept")
        return name, None, None

    def _split_dash(self, name: str) -> tuple[str, str | None, str | None] | None:
        # Dash-separated venue/unit pairs ("Friemanin talo -
        # nuorisotoimisto"); translation dashes split earlier, lowercase
        # descriptors strip in cleaning.
        if " - " not in name:
            return None
        left, _, right = name.partition(" - ")
        left, right = left.strip(), right.strip()
        if not left or not right:
            return None
        if re.search(
            r"(toimisto|kerho|ryhmä|klubi|piste|koulu|talo|keskus|asema|neuvonta|ohjaus|apteekki|kahvila)",
            right.lower(),
        ) and self._has_fixture(left):
            if re.search(r"(koulu|lukio|opisto|skola)", right.lower()):
                # School-headed right sides ("Kaukajärven koulu - Annalan
                # koulutalo") are same-institution buildings, not hosted
                # units: keep whole rather than housing a school in itself.
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
            return right[0].upper() + right[1:], self._clean_located(left) or left, name
        return None

    def _split_bare(self, name: str) -> tuple[str, str | None, str | None]:
        # Bare slash: compounds without spaces stay whole (Geo/on),
        # hyphen fragments never split (hiekka-/jääkenttä).
        head, _, tail = name.rpartition("/")
        head, tail = head.strip(), tail.strip()
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
            if tail[:1].isupper() and self._venue_tail(tail):
                self._count("name/slash_operator_unit")
                return tail, None, name
            self._count("name/slash_operator_head")
            return head, None, name
        if head and tail and self._is_street_head(head):
            # Bare street heads are never venues either.
            self._count("name/slash_street_head")
            return tail, None, name
        if head and tail:
            tail_base = tail.split(",")[0].strip()
            if re.search(r"(koulun|lukion|opiston|kodin)$", head.lower()) and self._room_tail(tail_base):
                # Genitive institution heads with room tails name one
                # facility ("Keuruun yläkoulun/lukion tanssisali"): keep
                # whole rather than strand a genitive fragment.
                self._count("name/slash_genitive_kept")
                return name, None, None
            if any(word in tail_base.lower() for word in self.SERVICE_TAILS) and self._has_fixture(head):
                # Hosted service units ("Töölön seniorikeskus/Helmi
                # ryhmäkoti"): the unit names the POI, the host the venue.
                self._count("name/slash_service_unit")
                return tail, self._clean_located(head) or head, name
        if (
            head
            and tail
            and " " in head
            and " " in tail
            and not head.endswith(("-", "/"))
            and not tail.startswith(("-", "/"))
            and len(head) > 1
            and len(tail) > 1
        ):
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
            tail_base = tail.split(",")[0].strip()
            if (
                "," in tail
                and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", tail_base)
                and re.search(r"(puisto|keskus|halli|kenttä|stadion|areena|talo|koulu)$", head.lower())
            ):
                # Compound facility names ("...Keinupuisto/Hilpi,
                # Hämeenlinna, ..."): don't split the facility; comma
                # dispatch strips the city/service tails instead.
                return None
            if not (self._has_fixture(head) or self._has_fixture(tail)):
                # No venue evidence on either side: co-titles stay whole.
                self._count("name/slash_venue_kept")
                return name, None, None
            self._count("name/slash_venue")
            return head, self._clean_located(tail), name
        self._count("name/slash_kept")
        return name, None, None

    def _venue_tail(self, tail: str) -> bool:
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

    def _split_inessive(self, name: str, tokens: list[str]) -> tuple[str, str | None, str | None] | None:
        # Services hosted AT a venue ("Martat neuvoo Kuusankosken
        # kirjastossa"): exact inessive venue nouns de-inflect to a
        # nominative located_in. Genitive-headed phrases stay whole.
        last = tokens[-1].lower()
        for stem in (
            "kirjasto",
            "koulu",
            "lukio",
            "museo",
            "kirkko",
            "kappeli",
            "opisto",
            "sairaala",
            "uimahalli",
            "nuorisotalo",
        ):
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
                    r"(koulu|lukio|opisto|päiväkoti|kirjasto|museo|kirkko|sairaala|neuvola)", head.lower()
                )
                and any(not t.lower().endswith("n") for t in head.split())
            ):
                self._count("name/inessive_host")
                return head, f"{venue_token} {host}", name
            break
        return None

    def _split_name(self, name: str, city: str | None = None) -> tuple[str, str | None, str | None]:
        # Returns (name, located_in, official_name). Dispatches to the
        # spaced-slash chain splitter, then bare-slash and comma shapes.
        if (split := self._split_machine(name)) is not None:
            return split
        if (split := self._split_paren(name, city)) is not None:
            return split
        if (split := self._split_dash(name)) is not None:
            return split
        if ":" in name and "://" not in name:
            if (split := self._split_colon(name, city)) is not None:
                return split
        if (m := re.match(r"(oysin|tyksin|husin|taysin|kysin)\s+(.+)$", name, flags=re.IGNORECASE)) and m.group(
            2
        ).strip():
            # Hospital acronym prefixes ("OYSin Keuhkosairauksien poliklinikka").
            self._count("name/acronym_prefix_venue")
            return m.group(2).strip(), m.group(1)[:-2].upper(), name
        tokens = name.split()
        if len(tokens) >= 3:
            if (split := self._split_inessive(name, tokens)) is not None:
                return split
        if (split := self._split_slash(name)) is not None:
            shown, located, official = split
            if " / " in shown:
                return self._resolve_nested(shown, located, official, name)
            return split
        if "/" in name and name.count("/") == 1:
            # Bare-slash guards may decline (compound facilities): fall
            # through to comma shapes instead of stranding None.
            if (split := self._split_bare(name)) is not None:
                return split
        if (split := self._split_name_tail(name, city)) is not None:
            return split
        return name, None, None

    def _split_name_tail(self, name: str, city: str | None) -> tuple[str, str | None, str | None] | None:
        # Space-separated city tails, fused school heads, Swedish venues
        # and comma shapes, in that precedence.
        if city and " " in name and "," not in name:
            head, _, tail = name.rpartition(" ")
            if (
                head.strip()
                and tail
                and re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", tail)
                and tail.casefold() == city.strip().casefold()
            ):
                # Space-separated city tails ("Kuntoutusohjaus Kankaanpää"):
                # the city repeats the structured address. No branch: it
                # would duplicate the city. Brand-embedded cities
                # ("International House Rauma", "SavoGrow Pielavesi") keep
                # the whole; generic activity heads ("Avoin jumpparyhmä
                # Kouvola") strip like venues do.
                stripped_head = head.strip()
                if re.search(r"\b(of|av|de|von|van|di|da|le|la)$", stripped_head, flags=re.IGNORECASE):
                    # The city completes a foreign proper name
                    # ("International School of Helsinki"): stripping
                    # leaves a dangling preposition, so keep the whole.
                    self._count("name/space_city_kept")
                elif self._has_fixture(stripped_head) or self._category(stripped_head)[0] is not None:
                    self._count("name/space_city")
                    return stripped_head.rstrip("|/,").strip() or stripped_head, None, name
                if self._is_proper_tail(stripped_head) or (
                    re.fullmatch(r"[A-ZÅÄÖ][A-Za-zåäö-]+", stripped_head) and not self._has_fixture(stripped_head)
                ):
                    self._count("name/space_city_kept")
                else:
                    self._count("name/space_city")
                    return stripped_head.rstrip("|/,").strip() or stripped_head, None, name
        if "," not in name and "/" not in name and ":" not in name:
            if (split := self._split_fused_school(name)) is not None:
                return split
        if "," in name:
            return self._split_comma(name, city)
        return None

    FUSED_ANCHORS = ("luokka", "luokat")

    def _split_fused_school(self, name: str) -> tuple[str, str | None, str | None] | None:
        # Comma-less "<Place-gen> <school-gen> <service/facility>" heads
        # ("Renkomäen koulun vaativan monimuotoisen tuen luokat"): the
        # unit names the POI, the school the venue. Anchored on service,
        # room and unit words so bare school phrases stay whole.
        tokens = name.split()
        if len(tokens) < 3:
            return None
        venue = None
        for genitive, nominative in self.SCHOOL_GENITIVE:
            if tokens[1].lower().endswith(genitive):
                venue = f"{tokens[0]} {tokens[1][: -len(genitive)] + nominative}"
                break
        if venue is None:
            return None
        rest = " ".join(tokens[2:])
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
        return rest[0].upper() + rest[1:], venue, name

    def _split_colon(self, name: str, city: str | None) -> tuple[str, str | None, str | None] | None:
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
    # plain social facility. Rescue only, never overrides a name mapping.
    CARE_HOUSING_RE = re.compile(r"asumi")
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

    def _resolve_fallback_category(self, item: Feature, channel: dict):
        # Category for channels the name leaves generic: linked-service
        # and ontology rescue first, description rescue next, generic last.
        # Returns the resolved category (or None for extras-only rescue).
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

    # Event/activity nouns: care rescue describes their purpose, never
    # their type ("Nakkifiesta" with mental-health ontology stays generic).
    ACTIVITY_RE = re.compile(
        r"(verstas|fiesta|juhla|festivaali|karnevaali|kilpailu|turnaus|ottelu|konsertti|näytelmä|kurssi|leiri|tapahtuma)"
    )

    def _rescue_blocked(self, channel: dict) -> bool:
        # Names rescue never types: utility buildings (typed by hosted
        # services otherwise) and fixed orienteering controls (typed by
        # shooting-ontology dumps otherwise). Both stay generic.
        fi = (self._names(channel).get("fi") or "").lower()
        return "huoltorakennus" in fi or "kiintorasti" in fi

    def _rescue_candidates(self, channel: dict) -> list:
        # Feed strings that can type an opaque channel, in precedence
        # order: linked services, ontology terms, translated names.
        candidates = []
        for row in channel.get("services") or []:
            name = ((row or {}).get("service") or {}).get("name")
            if name:
                candidates.append(name)
        for term in channel.get("ontologyTerms") or []:
            for term_name in (term or {}).get("name") or []:
                if term_name.get("language") == "fi" and term_name.get("value"):
                    candidates.append(term_name["value"])
        for row in channel.get("serviceChannelNames") or []:
            # Translated names often type opaque Finnish ones ("Daghemmet
            # Karitsa" → kindergarten); untranslated copies fall through.
            if isinstance(row, dict) and row.get("language") not in ("fi", None):
                value = (row.get("value") or "").strip()
                if value:
                    candidates.append(value)
        return candidates

    def _rescue_service(self, channel: dict) -> tuple | None:
        # Linked PTV services and YSO ontology terms type opaque channels
        # ("Maya", "Coxa") from feed data. Rescue-tier only: the channel
        # name already failed, so the first non-generic hit wins. Admin
        # units ("Liikunnan ja urheilun tulosyksikkö") match nothing and
        # fall through to the description rescue below.
        if self._rescue_blocked(channel):
            return None
        candidates = self._rescue_candidates(channel)
        activity = self.ACTIVITY_RE.search(self._clean_name(self._names(channel).get("fi") or "").lower())
        ward_name = self.SUBUNIT_RE.search(self._clean_name(self._names(channel).get("fi") or "").lower())
        if any(word in (c or "").lower() for c in candidates for word in ("ulkoilusaari", "ulkoilusaaret")):
            # Outdoor-island channels ("Porsas" with Ulkoilusaaret
            # services) are islands, whatever the first service types.
            self._count("category/rescued_island")
            return None, {"place": "island"}
        for candidate in candidates:
            category, extra = self._category(self._clean_name(candidate))
            if extra == {"place": "island"}:
                # Islands ride along in translated names ("...explosionen
                # på Skanslandet..."); the Finnish name carries the tag.
                continue
            if activity and extra is None and category in (Categories.CLINIC, Categories.SOCIAL_FACILITY):
                # Care-typed rescue on activity-named channels describes
                # purpose, not type ("Nakkifiesta" with mental-health
                # ontology stays generic).
                continue
            if extra or (category is not None and category != Categories.OFFICE_GOVERNMENT):
                # Specific types rescue; offices wait for the second pass so
                # a desk label never shadows a real type from a later
                # candidate ("päiväkotihoito" behind "Asiakaspalvelu").
                if category == Categories.HOSPITAL and ward_name:
                    # Ward-named channels ("Raaseporin TK vuodeosasto")
                    # are units, never hospitals, whatever the service.
                    return Categories.CLINIC, extra
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
        for term in channel.get("ontologyTerms") or []:
            for term_name in (term or {}).get("name") or []:
                if term_name.get("language") == "fi" and term_name.get("value"):
                    value = term_name["value"].lower()
                    if "taide" in value or "veistos" in value or "museo" in value:
                        return True
        return False

    def _rescue_category(self, channel: dict):
        text = self._description_text(channel)
        if not text:
            return None
        if self._rescue_blocked(channel):
            # Utility buildings and orienteering controls stay generic
            # whatever the description says.
            return None
        if any(word in text for word in self.CARE_WORDS):
            if self.CARE_HOUSING_RE.search(text):
                return Categories.ASSISTED_LIVING
            return Categories.SOCIAL_FACILITY
        if self.ART_RE.search(text):
            # Documented public art with an opaque name ("Kala ja poika").
            return Categories.TOURISM_ARTWORK
        return None

    def _split_comma_street_head(
        self, head: str, tail: str, name: str, city: str | None
    ) -> tuple[str, str | None, str | None] | None:
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
        if not re.search(
            r"(tie|katu|kuja|polku|väylä|raitti|kaari|penger|esplanadi|bulevardi" r"|vägen|väg|gatan|gata|gränd|stig)$",
            m.group(1).strip().lower(),
        ):
            return None
        self._count("name/comma_street_head")
        return tail, None, name

    def _split_comma_tail(
        self, head: str, tail: str, name: str, city: str | None
    ) -> tuple[str, str | None, str | None] | None:
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
            and not self._has_fixture(tail)
        ):
            # Multi-municipality coverage lists ("Kuntoutusohjaus,
            # Kaarina, Lieto, ..."): peel trailing towns and keep
            # peeling; the full form survives in official_name.
            self._count("name/comma_coverage_list")
            sub = self._split_comma(head, city)
            return sub[0], sub[1], name
        return None

    def _split_comma(self, name: str, city: str | None = None) -> tuple[str, str | None, str | None]:
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
            if (tail_hit := self._split_comma_tail(head, tail, name, city)) is not None:
                return tail_hit
            lowered_tail = tail.lower()
            lowered_head = head.lower()
            if len(tail) >= 7 and re.search(
                r"(tie|katu|kuja|polku|väylä|raitti|kaari|penger|esplanadi|bulevardi"
                r"|vägen|väg|gatan|gata|gränden|gränd|stigen|stig|väli|kurvi)$",
                lowered_tail,
            ):
                # Bare street tails are addresses, never venues
                # ("Kouluravintola, ..., Kenttäpolku"). Length-guarded:
                # short names ("Stig") are not streets.
                self._count("name/comma_street_tail")
                return head, None, name
            if (mid := self._split_comma_mid(head, tail, lowered_head, lowered_tail, name, city)) is not None:
                return mid
            if city and tail.casefold() == city.strip().casefold():
                # The tail repeats the structured post office
                # ("Kiikoisten lähitori, Sastamala").
                self._count("name/comma_city")
                return head, None, name
            if (street_head := self._split_comma_street_head(head, tail, name, city)) is not None:
                return street_head
            if re.fullmatch(r"[A-ZÅÄÖ][\w.-]*:?(lla|llä|ssa|ssä|sta|stä|lta|ltä)", tail) and not self._has_fixture(
                tail
            ):
                # Inflected place-name tails are coverage ("..., K-U:lla"),
                # not venues.
                self._count("name/comma_coverage_inflected")
                return head, None, name
            if re.search(r"poliisi", head.lower()) and not any(
                word in tail.lower()
                for word in (
                    "palvelu",
                    "toiminta",
                    "hoito",
                    "huolto",
                    "työ",
                    "tuki",
                    "neuvonta",
                    "ohjaus",
                    "kahvila",
                    "ravintola",
                    "kioski",
                    "kauppa",
                )
            ):
                # Police-station desk qualifiers (löytötavarat, lupapalvelut,
                # asetarkastus, aseen esitys) belong in the name: desk
                # counters are not separate venues, and branch=* is not
                # for stations. Unifies the three observed handlings.
                self._count("name/comma_police_desk_kept")
                return name, None, None
            if any(lowered_head.endswith(word) for word in self.SERVICE_HEADS):
                # Hosted services without a school-worded host (Norlandia
                # Linna): the service still names the POI, the host the
                # venue. Coverage tails still drop via the service split.
                if not (" ja " in tail and not self._has_fixture(tail) and not re.search(r"\d", tail)):
                    self._count("name/comma_service_host")
                    return head, self._clean_located(tail) or tail, name
            if (service := self._split_comma_service(head, tail, name, city)) is not None:
                return service
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

    def _split_comma_mid(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> tuple[str, str | None, str | None] | None:
        # Hosted-unit, branch-qualifier, city-first and service-head
        # comma pairs. Returns None to fall through to city tails and
        # the service split.
        if any(word in lowered_tail for word in self.UNIT_TAILS) and self._is_institution(head.lower()):
            self._count("name/comma_unit")
            return tail, self._clean_located(head), name
        if any(word in lowered_tail for word in self.BRANCH_TAILS):
            # Campus/desk qualifiers are part of the signed name
            # ("Stadin ammattiopisto, Roihupellon toimipaikka"): OSM
            # branch=* is chain-retail with brand=*, not schools, and
            # the short form is not derivable without morphology, so
            # the full form stays the name (cf. way/1094085495).
            self._count("name/comma_branch_kept")
            return name, None, None
        if tail.lower() in self.SERVICE_HEADS and re.search(r"(koulu|lukio|opisto)", lowered_head):
            # School-hosted health services ("Merilahden peruskoulu,
            # Jaluspolun toimipiste, kouluterveydenhuolto"): the service
            # names the POI, the school hosts it (cf. service@school).
            self._count("name/comma_school_health_service")
            shown = tail[0].upper() + tail[1:] if tail else tail
            return shown, self._clean_located(head) or head, name
        if self._room_tail(lowered_tail) and self._is_institution(head.lower()):
            # Facility rooms/fields at institutions ("Vaajakummun koulu,
            # luistelukenttä"): the room names the POI (cf. slash_room).
            self._count("name/comma_room")
            return tail, self._clean_located(head), name
        if city and head.casefold() == city.strip().casefold():
            # City-first records ("Vaasa, Ulosottolaitos").
            self._count("name/comma_city_head")
            return tail, None, name
        if any(lowered_head.endswith(word) for word in self.SERVICE_HEADS) and self.SCHOOL_TAIL_RE.search(tail.lower()):
            self._count("name/comma_service_venue")
            return head, self._clean_located(tail), name
        if any(lowered_head.endswith(word) for word in self.SERVICE_HEADS):
            # Fused genitive shape ("Rovastinkankaan koulun
            # opiskeluhuolto, Orivesi"): the service names the POI,
            # the school is the venue (cf. the service-map
            # school-head/service-tail rule, word order inverted).
            if (venue := self._genitive_school(head)) is not None:
                self._count("name/comma_service_genitive")
                return head.split()[-1].capitalize(), venue, name
        return None

    def _split_comma_school_host(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str
    ) -> tuple[str, str | None, str | None] | None:
        # Group activities hosted at schools ("Lempeä selkäjooga-ryhmä,
        # Veittijärven koulu"): the school locates the activity instead
        # of typing it. Daycare hosts stay whole (the daycare is the venue).
        if (
            re.search(r"(koulu|lukio|opisto|päiväkoti)$", lowered_tail)
            and self._custom_group_use(lowered_head) is not None
            and not re.search(r"(koulu|lukio|opisto|päiväkoti)", lowered_head)
        ):
            self._count("name/comma_school_host")
            return head, self._clean_located(tail) or tail, name
        return None

    def _split_comma_service_head(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str
    ) -> tuple[str, str | None, str | None] | None:
        # Service-headed pairs ("Perhekeskus, Suvituuli") and hospital
        # wards ("Raskauden seurantaosasto, Tyks Majakkasairaala"): the
        # head names the POI, the venue hosts it (wards cf.
        # comma_service_unit for yksikkö units). Lowercase service tails
        # without institution words or proper nouns drop instead
        # (descriptor branch below).
        if (
            any(word in lowered_head for word in self.SERVICE_TAILS)
            and self._has_fixture(tail)
            and (not self._is_unit_tail(tail) or self._is_venue_head(head))
            and (not self._is_unit_tail(head) or self._is_venue_head(tail))
            and (
                tail[:1].isupper()
                or re.search(r"(koulu|lukio|opisto|päiväkoti|kirjasto|museo|sairaala|neuvola)", lowered_tail)
                or re.search(r"\s[A-ZÅÄÖ]", tail)
            )
        ):
            self._count("name/comma_service_unit")
            shown = head[0].upper() + head[1:] if head else head
            return shown, self._clean_located(tail), name
        if re.search(r"\w*osasto$", lowered_head) and re.search(
            r"(sairaala|terveyskeskus|terveysasema|mielenterveyskeskus)$", lowered_tail
        ):
            self._count("name/comma_ward_venue")
            return head, self._clean_located(tail) or tail, name
        return None

    def _split_comma_unit_venue(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> tuple[str, str | None, str | None] | None:
        # Venue-headed service pairs ("Perhekeskus, Suvituuli"): the tail
        # service names the POI, the venue head hosts it.
        if (
            any(word in lowered_tail for word in self.SERVICE_TAILS)
            and (self._has_fixture(head) or (self._is_proper_tail(head) and not self._is_person(head)))
            and not re.search(r"\b(oy|ab)\b", head, flags=re.IGNORECASE)
            and not self._is_private_org(head)
            and (not self._is_unit_tail(tail) or self._is_venue_head(head))
            and (not self._is_unit_tail(head) or self._is_venue_head(tail))
        ):
            self._count("name/comma_unit_venue")
            shown = tail[0].upper() + tail[1:] if tail else tail
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
            return self._clean_located(head) or head
        sub = self._split_comma(head, city)
        if sub[1] is None and sub[0] != head:
            return sub[0]
        return head

    def _split_comma_keep_whole(self, head: str, tail: str, name: str) -> tuple[str, str | None, str | None] | None:
        # Coverage areas and organisation desks keep the signed form whole,
        # never split into located_in (cf. Stadin, police desks).
        lowered_head, lowered_tail = head.lower(), tail.lower()
        if self._is_bare_area(head) or self._is_bare_area(tail):
            # Bare coverage areas ("Puheterapia, Tikkurilan alue").
            self._count("name/comma_area_kept")
            return name, None, None
        if lowered_tail.endswith("vastaanotto") and any(
            lowered_head.endswith(word) for word in ("toimisto", "virasto", "kaupunki", "kunta")
        ):
            # Desks of offices and municipalities ("Pirkanmaan
            # oikeusaputoimisto, Valkeakosken vastaanotto"): the
            # organisation is not a venue.
            self._count("name/comma_office_desk_kept")
            return name, None, None
        return None

    def _split_comma_service(
        self, head: str, tail: str, name: str, city: str | None
    ) -> tuple[str, str | None, str | None] | None:
        # Service/unit comma pairs, both directions, then tail cleaners.
        lowered_head, lowered_tail = head.lower(), tail.lower()
        if (kept := self._split_comma_keep_whole(head, tail, name)) is not None:
            return kept
        if (school_host := self._split_comma_school_host(head, tail, lowered_head, lowered_tail, name)) is not None:
            return school_host
        if re.search(r"vapaa-aika ?talo$", lowered_tail) and self._has_fixture(head):
            # Leisure-house venues ("Kuntosali, Kaukajärven vapaa-aika
            # talo"): the service/room head names the POI, the house
            # hosts it.
            self._count("name/comma_leisure_house")
            return head, self._clean_located(tail) or tail, name
        if (svc_unit := self._split_comma_service_head(head, tail, lowered_head, lowered_tail, name)) is not None:
            return svc_unit
        if (unit_venue := self._split_comma_unit_venue(head, tail, lowered_head, lowered_tail, name, city)) is not None:
            return unit_venue
        return self._split_comma_tail_rest(head, tail, lowered_head, lowered_tail, name, city)

    def _split_comma_tail_rest(
        self, head: str, tail: str, lowered_head: str, lowered_tail: str, name: str, city: str | None
    ) -> tuple[str, str | None, str | None] | None:
        # Lowercase descriptors, Swedish tails, proper/unit venues and
        # coverage tails resolve after the service/unit dispatch above.
        if (
            tail
            and tail[0].islower()
            and any(word in lowered_tail for word in ("palvelu", "toiminta", "hoito", "huolto", "työ", "tuki"))
            and not re.search(r"(koulu|lukio|opisto|päiväkoti|kirjasto|museo|sairaala|neuvola)", lowered_tail)
        ):
            # Lowercase service descriptors ("Teuvolan vammaisten
            # asumispalvelut, tilapäishoito ja loma-ajanhoito"): the head
            # names it, the tail is no venue. Comma heads resolve further
            # ("Ikifit Oy, ...Keinupuisto/Hilpi, Hämeenlinna, ...").
            self._count("name/comma_descriptor_dropped")
            if "," in head:
                sub = self._split_comma(head, city)
                return sub[0], sub[1], name
            return head, None, name
        if any(word in lowered_tail for word in self.SWEDISH_SERVICE_TAILS) and self._is_institution(head.lower()):
            # Swedish service tails ("Zacharias Topeliusskolan,
            # Smågruppsundervisning"): the service names the POI.
            self._count("name/comma_unit_venue_sv")
            return tail, self._clean_located(head) or head, name
        if re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", tail) and self._is_institution(head.lower()):
            if re.search(r"(koulu|lukio|opisto|päiväkoti|esiopetus|yläaste|ala-aste|skola|daghem)", head.lower()):
                # Named units hosted at schools ("Sipoon lukio, Enter").
                # Localities at other institutions ("Kalvolan neuvola,
                # Iittala") stay whole: no gazetteer distinguishes them.
                self._count("name/comma_unit_proper")
                return tail, self._clean_located(head) or head, name
            self._count("name/comma_unit_locality_kept")
            return name, None, None
        if re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", tail) and self._has_fixture(tail):
            # Named venues host the head service ("Neuvonta, Reimasali").
            self._count("name/comma_proper_venue")
            return head, self._clean_located(tail), name
        if (
            re.fullmatch(r"[A-ZÅÄÖ][a-zåäö-]+", tail)
            and tail.lower().endswith(("järvi", "lampi", "saari", "luoto", "joki", "koski"))
            and self._has_fixture(head)
        ):
            # Lakes and waters name venues ("Vojakkalan uimapaikka,
            # Kaartjärvi"): the facility names the POI, the water hosts it.
            self._count("name/comma_water_venue")
            return head, self._clean_located(tail) or tail, name
        if len(tail) >= 3 and tail.upper() in self.HOSPITAL_ACRONYMS:
            # Hospital acronyms are venues ("... osasto J1, Tyks").
            self._count("name/comma_acronym_venue")
            return head, tail, name
        if (
            self._has_fixture(head)
            and self._is_proper_tail(tail)
            and re.search(
                r"(puisto|koulu|kirjasto|museo|kirkko|kappeli|tori|kenttä|ranta|satama|asema"
                r"|lukio|opisto|päiväkoti)",
                tail.lower(),
            )
        ):
            # Facilities at proper-named venues ("Kahluuallas, Leikkipuisto
            # Traktori"): the facility names the POI (cf. slash_room).
            self._count("name/comma_facility_venue")
            return head, self._clean_located(tail), name
        if " ja " in tail and not self._has_fixture(tail) and not re.search(r"\d", tail):
            if head.rstrip().endswith("-"):
                # Hyphen-fragment lists ("Sovellettua jooga-, pilates- ja
                # faskiaharjoittelua") are one name, not coverage areas.
                return None
            # Municipality-coverage tails ("Kotihoito, Oulainen ja Merijärvi").
            self._count("name/comma_coverage_dropped")
            return head, None, name
        if re.fullmatch(r"osasto\s*\d+\.?$", tail, flags=re.IGNORECASE):
            # Internal department numbers ("Katriinan toimipiste, osasto 5").
            self._count("name/comma_dept_dropped")
            return head, None, name
        if (
            tail
            and tail[0].islower()
            and any(word in tail.lower() for word in ("palvelu", "toiminta", "hoito", "huolto", "työ", "tuki"))
        ):
            # Lowercase service descriptors ("..., ostopalvelut"). Other
            # lowercase tails (qualifiers like "åk 1–2") stay whole.
            self._count("name/comma_descriptor_dropped")
            return head, None, name
        return None

    PHONE_HINT_RE = re.compile(r"(puhelin|phone|telefon)", re.IGNORECASE)
    ZW_RE = re.compile("[\u200b-\u200d\ufeff\u00ad]")
    # Switchboard/central contacts stamped across locations are not
    # per-store data (cf. the JSON-LD hotline lesson): drop on sight.
    GENERIC_PHONES = frozenset({"358981621", "358983911"})  # Espoon/Vantaan vaihteet
    GENERIC_EMAILS = frozenset({"info@esperi.fi"})  # Central corporate inbox
    LOGIN_URL_RE = re.compile(r"(authentication|/login\b|^https?://menu\.)", re.IGNORECASE)

    @classmethod
    def _visible(cls, text: str) -> str:
        return cls.ZW_RE.sub("", text)

    def _entry_is_phone(self, entry: dict) -> bool:
        for row in entry.get("additionalInformation") or []:
            if isinstance(row, dict) and self.PHONE_HINT_RE.search(row.get("value") or ""):
                return True
        return False

    @staticmethod
    def _to_minutes(value) -> int | None:
        match = re.match(r"^(\d{1,2}):(\d{2})", (value or "").strip())
        if not match:
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
            day = self.DAY_MAP.get((span.get("dayFrom") or "").upper())
            if not day:
                self._count("hours/unknown_day")
                continue
            if entry.get("isClosed"):
                closed_days.add(day)
                continue
            days = [day]
            last = self.DAY_MAP.get((span.get("dayTo") or "").upper())
            if last and last != day:
                # Multi-day span (Monday - Friday): expand the range.
                order = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")
                days = (
                    order[order.index(day) : order.index(last) + 1] if order.index(last) > order.index(day) else [day]
                )
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

    def _hours(self, channel: dict, category=None) -> OpeningHours | str | None:
        # Staff timetables arrive per service desk (nurse, counsellor,
        # psychologist, phone): buffer spans per weekday, drop phone-only
        # sets, union-merge overlaps, then render once. Deterministic
        # regardless of entry order (closed marks lose to real spans).
        oh = OpeningHours()
        day_spans: dict[str, list[tuple[int, int, bool]]] = {}
        closed_days: set[str] = set()
        always_open = False
        for entry in channel.get("serviceHours") or []:
            if not isinstance(entry, dict):
                continue
            if entry.get("serviceHourType") not in ("DaysOfTheWeek", "OverMidnight"):
                # Exceptional single-date rules are deviations, not timetables.
                # OverMidnight carries ordinary day ranges under an on-call
                # label (cf. pharmacy päivystys hours) and parses the same way.
                self._count("hours/skipped_type/" + str(entry.get("serviceHourType") or "missing"))
                continue
            if entry.get("validFrom") or entry.get("validTo"):
                # Dated rules are deviations, never the timetable.
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
        if always_open:
            if (
                category in (Categories.SOCIAL_FACILITY, Categories.SCHOOL, Categories.COLLEGE, Categories.KINDERGARTEN)
                and not day_spans
            ):
                # Staffed-around-the-clock care homes and schools are not
                # publicly walk-in 24/7; a 24/7 tag would mislead.
                self._count("hours/skipped_always_open_social")
                return None
            for day in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"):
                oh.add_range(day, "00:00", "23:59", time_format="%H:%M")
            # Around-the-clock opening renders as a plain 24/7 string
            # (cf. other spiders), never overlapping spans.
            return "24/7"
        for day in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"):
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

    SUBUNIT_RE = re.compile(r"(osasto|yksikkö|vastaanotto|klinikka|sosialityö|sosiaalityö|säilytys)")

    def _custom_category(self, name_fi: str) -> tuple | None:
        # Pre-table rules: unambiguous machines, shore/market guards and
        # scoped overrides the keyword table cannot express.
        lowered = name_fi.lower()
        if (machine := self._custom_machine(name_fi, lowered)) is not None:
            return machine
        if (tori := self._custom_tori(lowered)) is not None:
            return tori
        if (shore := self._custom_shore(lowered)) is not None:
            return shore
        if (health := self._custom_health(name_fi, lowered)) is not None:
            return health
        if re.search(r"(kirkko|kappeli)$", lowered) and not re.search(
            r"(ortodoks|katol|helluntai|vapaakirkko|advent|baptist|metodist|mormoni|jehov|anglikaan)", lowered
        ):
            # Finnish parish churches are Evangelical Lutheran unless signed otherwise.
            return Categories.PLACE_OF_WORSHIP, {"religion": "christian", "denomination": "lutheran"}
        if (ward := self._custom_ward(lowered)) is not None:
            return ward
        if (group := self._custom_group_use(lowered)) is not None:
            return group
        if (ground := self._custom_exercise_ground(lowered)) is not None:
            return ground
        return None

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
    SHORE_FACILITY_BAIL = (
        "kenttä",
        "volley",
        "pallo",
        "kaukalo",
        "luistelu",
        "sali",
        "halli",
        "koulu",
        "lukio",
        "opisto",
        "päiväkoti",
        "kirjasto",
        "museo",
        "kirkko",
        "kappeli",
        "sairaala",
        "neuvola",
        "terveysasema",
        "vastaanotto",
        "eläinlääkäri",
        "toimisto",
        "virasto",
        "poliisi",
        "apteekki",
        "teatteri",
        "kotihoito",
        "hoiva",
        "lyhytaikais",
        "asumispalvelu",
        "huoltorakennus",
        "rakennus",
        "leikki",
        "kalastus",
        "koirauimaranta",
        "ulkokuntoilu",
        "kuntoilupiste",
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

    def _custom_shore(self, lowered: str) -> tuple | None:
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
            re.search(r"(?:\bsatama\b|\w+satama\b)", lowered)
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
                # Managed winter-swimming beaches are swimming areas.
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

    def _custom_tori(self, lowered: str) -> tuple | None:
        # Market squares, with guards for lookalike compounds. Returns
        # None to fall through to the table (parking), (None, extra) for
        # placement-only squares, or a category.
        if not self.TORI_RE.search(lowered) or re.search(
            r"(lähitori|konttori|kuraattori|koordinaattori|kirpputori|navigaattori|palvelutori"
            r"|traktori|pastori|kanttori|reaktori)",
            lowered,
        ):
            # Lähitori (senior centres), konttori (offices), kuraattori
            # (counsellors), koordinaattori (coordinator desks), kirpputori
            # (flea markets), Navigaattori and Palvelutori (service desks)
            # end in tori without being squares, as do tractors, pastors,
            # cantors and reactors.
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

    def _custom_ward(self, lowered: str) -> tuple | None:
        if re.search(r"(?:^|[\s-])osasto(?=\s|$)", lowered):
            # Bare wards/departments ("Malmin osasto 13", "Keuhko-osasto"):
            # hospital departments, not hospitals. Separator-anchored so
            # Kaupunginosa and Viestintäosasto never match.
            return Categories.CLINIC, None
        return None

    def _custom_group_use(self, lowered: str) -> tuple | None:
        # Inessive host nouns ("Kuusankosken kirjastossa") and group-noun
        # compounds (teatteriryhmä, kirjastoparlamentti) describe a service
        # or activity, never the venue: fall through to generic. Peer-support
        # groups (vertaisryhmä, vertaistukiryhmä) and senior clubs
        # (seniorikerho) are venues and file via the keyword table instead. Bare group numbers ("Kuntosali, ryhmä 1") leave the
        # venue filing alone; health contexts keep theirs.
        host_stems = (
            "kirjasto",
            "koulu",
            "lukio",
            "museo",
            "kirkko",
            "kappeli",
            "opisto",
            "sairaala",
            "uimahalli",
            "nuorisotalo",
        )
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
        if any(
            re.search(r"[\w-]+(ryhmä|kerho|kuoro|orkesteri|joukkue|parlamentti)$", token.strip(",.;:"))
            and token not in ("leikkikerho", "leikkikoulu")
            and "vertais" not in token
            and "seniori" not in token
            and "sydän" not in token
            and "asumis" not in token
            and "4h-kerho" not in token
            for token in lowered.split()
        ) and not re.search(
            r"(psykiatri|terapia|terveys|hoito|huolto|klinikka|sairaala|lääkäri|neuvola|mieli|päihde|vamma|hoiva|kuntout|rokot|hammas)",
            lowered,
        ):
            return None, None
        return None

    def _custom_exercise_ground(self, lowered: str) -> tuple | None:
        # Neighbourhood exercise grounds mirror the service-map activity
        # refinement: ball-game arenas are pitches, schoolyards read as
        # playgrounds (cf. Kungsgårdsskolan).
        if "lähiliikuntapaikka" not in lowered:
            return None
        if re.search(r"(miniareena|ministadion|pallopel|pallokentt|pelikentt|monitoimikentt)\w*", lowered):
            return Categories.LEISURE_PITCH, None
        if re.search(r"(koulu|skol)\w*", lowered):
            return Categories.LEISURE_PLAYGROUND, None
        return None

    def _carve_room_tail(self, name_fi: str):
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
            self._count("category/room_building_generic")
            return None, None
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

    def _category(self, name_fi: str):
        # Invisible characters (zero-width, soft hyphens) never carry
        # matching meaning; strip them so feed dirt can't hide keywords.
        name_fi = self._visible(name_fi)
        if (custom := self._custom_category(name_fi)) is not None:
            return custom
        if (carved := self._carve_room_tail(name_fi)) is not None:
            return carved
        lowered = name_fi.lower()
        # Gradation plurals/genitives never contain their singular
        # (kenttä/kentät/kentän, ranta/rannat/rannan, keskus/keskuksen,
        # seulonta/seulonnat/seulonnan, päiväkoti/päiväkodit/päiväkotien,
        # paikka/paikat/paikkojen): normalize the known stems first.
        lowered = re.sub(r"kentät\b", "kenttä", lowered)
        lowered = re.sub(r"kentän\b", "kenttä", lowered)
        lowered = re.sub(r"rannat\b", "ranta", lowered)
        lowered = re.sub(r"rannan\b", "ranta", lowered)
        lowered = re.sub(r"keskuksen\b", "keskus", lowered)
        lowered = re.sub(r"seulonnat\b", "seulonta", lowered)
        lowered = re.sub(r"seulonnan\b", "seulonta", lowered)
        lowered = re.sub(r"päiväkodit\b", "päiväkoti", lowered)
        lowered = re.sub(r"päiväkotien\b", "päiväkoti", lowered)
        lowered = re.sub(r"paikat\b", "paikka", lowered)
        lowered = re.sub(r"paikkojen\b", "paikka", lowered)
        lowered = re.sub(r"yhdistykset\b", "yhdistys", lowered)
        lowered = re.sub(r"taudit\b", "tauti", lowered)
        lowered = re.sub(r"tautien\b", "tauti", lowered)
        lowered = re.sub(r"radat\b", "rata", lowered)
        lowered = re.sub(r"yksiköt\b", "yksikkö", lowered)
        lowered = re.sub(r"veistokset\b", "veistos", lowered)
        lowered = re.sub(r"veistoksen\b", "veistos", lowered)
        lowered = re.sub(r"taideteokset\b", "taideteos", lowered)
        lowered = re.sub(r"taideteoksen\b", "taideteos", lowered)
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
        if raw.strip().startswith("+"):
            if digits.startswith("359") and len(digits) == 12:
                # Single-digit country typo on a Finnish number
                # ("+359 447301262" in Ikaalinen): repair to +358.
                self._count("contact/country_typo")
                digits = "358" + digits[3:]
            if not digits.startswith("358"):
                return raw.strip() or None
            digits = digits[3:].lstrip("0")
        else:
            if not digits.startswith("0"):
                return raw.strip() or None
            digits = digits.lstrip("0")
        if digits.startswith("358") and len(digits) > 10:
            # Duplicated country code from a feed concat ("+358 358...").
            digits = digits[3:]
        if not digits.isdigit() or not (5 <= len(digits) <= 10):
            self._count("contact/invalid_phone")
            return None
        if digits[0] in ("4", "5") and len(digits) >= 9:
            # Mobile prefixes stay readable ("+358 50 9119693").
            return "+358 " + digits[:2] + " " + digits[2:]
        if len(digits) <= 7:
            # Short landlines split the single-digit area ("+358 9 4711").
            return "+358 " + digits[:1] + " " + digits[1:]
        return "+358 " + digits

    def _apply_contact(self, item: Feature, channel: dict) -> None:
        phones = channel.get("phoneNumbers") or []
        if isinstance(phones, list) and phones and isinstance(phones[0], dict):
            number = (phones[0].get("number") or "").strip()
            prefix = (phones[0].get("prefixNumber") or "").strip()
            if number:
                if re.sub(r"\D", "", prefix + number) in self.GENERIC_PHONES:
                    self._count("contact/generic_hotline")
                else:
                    raw = f"{prefix} {number}".strip() if prefix else number
                    if normalized := self._normalize_phone(raw):
                        item["phone"] = normalized
        emails = channel.get("emails") or []
        if emails and isinstance(emails[0], dict) and emails[0].get("value"):
            email = emails[0]["value"].strip()
            local = email.split("@")[0].lower()
            if email.lower() in self.GENERIC_EMAILS:
                self._count("contact/generic_email")
            elif local in (
                "etunimi.sukunimi",
                "firstname.lastname",
                "nimi.sukunimi",
                "fornamn.efternamn",
                "förnamn.efternamn",
            ):
                # Template placeholders, never real contacts.
                self._count("contact/placeholder_email")
            else:
                item["email"] = email
        pages = channel.get("webPages") or []
        if pages and isinstance(pages[0], dict) and pages[0].get("url"):
            url = pages[0]["url"].strip()
            if self.LOGIN_URL_RE.search(url):
                # Login walls are never websites.
                self._count("contact/login_url")
            else:
                item["website"] = url

    # Housenumber with optional letter and range ("Katutie 2a" stays whole,
    # "Nummentie 12 - 14" folds to "12-14"). PTV-local copy of the
    # service-map token rules; the driver differs (split street/number
    # fields, comma/slash tails inside the number field).
    HOUSENUMBER_RE = re.compile(r"\d+[a-zA-Z]?(?:-\d+[a-zA-Z]?)?")
    # Staircase/room/door tails after a housenumber, in priority order:
    # (min tokens, housenumber offset, middle, last, flags, join).
    STAIRCASE_RULES = (
        (4, 3, r"\d+[A-Za-z]?", r"[A-Za-z]{1,2}", 0, "MID LAST"),
        (4, 3, r"[A-Za-z]", r"\d+(?:-\d+)?[A-Za-z]?", 0, "MID LAST"),
        (4, 3, r"[A-Za-z]", r"[A-Za-z]", 0, "MID-LAST"),
        (4, 3, r"(?i:as)", r"\d+[A-Za-z]?", re.IGNORECASE, "MID LAST"),
        (3, 2, None, r"[A-Za-z]{1,2}(?:-[A-Za-z]{1,2})?|\d+", 0, "LAST"),
        (3, 2, None, r"[A-Za-z]{1,2}\d+[A-Za-z]?|[A-Za-z]-(?:ovi|rappu)", re.IGNORECASE, "LAST"),
    )
    # Tails describing everything but the street address. Finnish floor
    # numbers never convert to OSM level, so they are dropped, not mapped.
    ADDR_STRIP_RULES = (
        (r"\s*\([^)]*\)", 0),
        (r",\s*[\d\s&\.,-]*(krs|kerros|vån|våning|rak\.?|rakennus)\b.*$", 0),
        (r"\s+\d+\.?\s*(krs|kerros|vån|våning)\b.*$", 0),
        (r"/\s*\d+\.?\s*(krs|kerros|vån|våning)\b.*$", 0),
        (r"\s+(rak\.?|rakennus|krs|kerros|vån|våning)\b.*$", 0),
        (r"\s+-\s*(sisään\w*|käynti\w*|sisäpiha|porras|ovi|entrance)\b.*$", re.IGNORECASE),
        (r"\s+vastapäätä[\s.!]*$", re.IGNORECASE),
    )
    # PO-box tails inside the number field ("Kolpintie 7, PL 111").
    POBOX_TAIL_RE = re.compile(r"pl\b.*$", re.IGNORECASE)
    # Building tails kept as units ("Kunnallissairaalantie 20, rakennus 7").
    BUILDING_TAIL_RE = re.compile(r"(\b(rak\.?|rakennus)\b|\w*talo\b)\s*[\w.]*$", re.IGNORECASE)
    # Stair/door/apartment tails kept as units ("2, A-ovi"; "11, A").
    UNITWORD_TAIL_RE = re.compile(
        r"([A-Za-z]\s+)?(asunto|\bas\b|rappu|huoneisto|liikehuoneisto|porras|ovi)\b\s*[\w.]*$", re.IGNORECASE
    )
    # Place suffixes for numberless addresses (squares, islands...), street
    # suffixes for bare streets. PTV-local copies of the service-map lists.
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
        "kari",
        "selkä",
        "laituri",
        "saaristo",
        "holme",
        "holmen",
        "viken",
        "sjö",
        "sjön",
        "parken",
        "torget",
        "skär",
    )
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
        "kurvi",
    )

    def _strip_addr_base(self, address: str) -> str:
        address = address.replace("­", "").replace("–", "-").replace("—", "-")
        base = address
        for pattern, flags in self.ADDR_STRIP_RULES:
            base = re.sub(pattern, "", base, flags=flags).strip()
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
        for min_len, offset, mid, last, flags, join in self.STAIRCASE_RULES:
            if len(tokens) < min_len:
                continue
            if not re.fullmatch(number, tokens[-offset]):
                continue
            if mid is not None and not re.fullmatch(mid, tokens[-2]):
                continue
            if not re.fullmatch(last, tokens[-1], flags):
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

    def _number_tail(self, tail: str) -> str | None:
        # Comma tails inside the number field resolve to units or dropped
        # descriptors; None drops.
        if re.search(r"(krs|kerros|vån|våning)\b", tail, flags=re.IGNORECASE):
            self._count("address/floor_tail")
            return None
        if re.match(r"\d{5}\b", tail):
            # Postcode leaked into the number field.
            self._count("address/postcode_in_unit")
            return None
        if self.POBOX_TAIL_RE.search(tail):
            self._count("address/pobox_dropped")
            return None
        if (
            self.BUILDING_TAIL_RE.search(tail)
            or self.UNITWORD_TAIL_RE.search(tail)
            or re.fullmatch(r"[A-Za-z]{1,2}(?:-(?:ovi|rappu))?", tail, flags=re.IGNORECASE)
            or re.search(r"\d", tail)
        ):
            self._count("address/comma_unit")
            return tail
        self._count("address/descriptor_dropped")
        return None

    def _number_parts(self, number: str) -> tuple[str, list[str]]:
        # Returns (core, units): slash venues and comma tails resolve first.
        # Postcode tails leak into the number field ("3 03100 Nummela").
        stripped = re.sub(r"\s*\b\d{5}\b\s*\S.*$", "", number).strip()
        if stripped != number.strip():
            self._count("address/postcode_in_number")
            number = stripped
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
            # Venue notes inside the number field ("/ Espoon Keskuspuisto").
            self._count("address/venue_tail_dropped")
        raw_head = number.partition("/")[0]
        head = re.sub(r"(?<!,)\s+((?:rak\.?|rakennus)\b)", r", \1", raw_head, flags=re.IGNORECASE).strip()
        if head != raw_head.strip():
            # Space-form building tails ("15 rak.1 B-rappu") resolve like
            # the comma form ("8, rak. N, B-rappu"): housenumber plus unit.
            self._count("address/building_tail")
        parts = [p.strip() for p in head.split(",") if p.strip()]
        core = parts[0] if parts else ""
        if core:
            district = re.match(r"^(\d+[A-Za-z]?(?:\s*-\s*\d+[A-Za-z]?)?)\s+([A-ZÅÄÖ][a-zåäö]{2,})$", core)
            if (
                district
                and not self.BUILDING_TAIL_RE.search(district.group(2))
                and not self.UNITWORD_TAIL_RE.search(district.group(2))
                and not re.fullmatch(r"[A-Za-z]{1,2}(?:-(?:ovi|rappu))?", district.group(2), flags=re.IGNORECASE)
                and not re.search(r"\d", district.group(2))
            ):
                # District tails inside the number field ("1 Alppiharju"):
                # the housenumber counts, the district drops.
                self._count("address/district_tail_dropped")
                core = district.group(1)
                parts = [core, *parts[1:]]
        if core:
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
            if (unit := self._number_tail(tail)) is not None:
                units.append(unit)
        return core, units

    # Island infixes routing numberless sites to addr:place
    # ("Talholmen virkistysalue", whose tail is not a place suffix).
    ISLAND_INFIX = ("saari", "luoto", "holm", "skär")

    def _route_placeless(self, item: Feature, raw: str) -> None:
        # Numberless roads: single-token non-streets and named places go to
        # addr:place, bare streets and the rest stay on the line.
        lowered = raw.lower()
        if len(raw.split()) == 1 and not lowered.endswith(self.STREET_SUFFIXES):
            self._count("address/place")
            item["extras"]["addr:place"] = raw
            return
        if lowered.endswith(self.PLACE_SUFFIXES):
            if raw.split()[-1].lower().endswith(("asema", "selkä", "laituri")):
                # Stations, open water and piers are not addr:place values.
                self._count("address/place_station")
                item["street_address"] = raw
            else:
                self._count("address/place")
                item["extras"]["addr:place"] = raw
            return
        if not lowered.endswith(self.STREET_SUFFIXES) and any(word in lowered for word in self.ISLAND_INFIX):
            # Island sites whose tail is a zone noun, not a place suffix
            # ("Talholmen virkistysalue").
            self._count("address/place_island")
            item["extras"]["addr:place"] = raw
            return
        self._count("address/bare_street" if lowered.endswith(self.STREET_SUFFIXES) else "address/freeform")
        if lowered.endswith(self.STREET_SUFFIXES):
            # Bare streets carry the street name with no number.
            item["street"] = raw
        else:
            item["street_address"] = raw

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
            if lowered.endswith(self.STREET_SUFFIXES):
                scored.append(2)
            elif lowered.endswith(self.PLACE_SUFFIXES):
                scored.append(1)
            else:
                scored.append(0)
        if max(scored) == 0:
            return road
        # Tie between two scored parts: prefer the tail (venue-prefix
        # order puts the road last); a lone scored head still wins.
        top = [i for i, s in enumerate(scored) if s == max(scored)]
        best = top[-1] if len(top) > 1 else top[0]
        if parts[best] != road:
            self._count("address/road_venue_prefix")
        return parts[best]

    def _strip_road_city(self, road: str | None, number: str, city_src: str | None) -> tuple:
        # City tails repeat the structured municipality, never the road:
        # the city leaked into the number field ("Tahtimarssi 3" with
        # number "Oulu") or rides the road line ("Pappilantie 11,
        # pielavesi", "Mäntymäentie 55, 13700 hattula").
        if number and city_src and not re.search(r"\d", number) and number.casefold() == city_src.strip().casefold():
            self._count("address/city_in_number")
            number = ""
        if road and "," in road and not number and city_src:
            head, _, tail = road.rpartition(",")
            tail = re.sub(r"^\d{5}\s+", "", tail.strip()).strip()
            if head.strip() and tail and tail.casefold() == city_src.strip().casefold():
                self._count("address/road_city_tail")
                road = head.strip()
        return road, number

    def _apply_address(self, item: Feature, street: dict, postcode: str | None, city_src: str | None) -> None:
        road = self._lang_value(street.get("street") or [], "fi", "sv", "en")
        number = (street.get("streetNumber") or "").strip()
        if road and road[0].islower():
            # Feed roads starting lowercase ("wetterhoffinkatu").
            self._count("address/road_case")
            road = road[0].upper() + road[1:]
        if road and re.match(r"^(pl|p\.l\.)\b", road.strip(), flags=re.IGNORECASE):
            # PO boxes filed as streets ("PL 52"): no visit address, but
            # the channel keeps its city, postcode and coords.
            self._count("address/pobox_road")
            road, number = None, ""
        road, number = self._strip_road_city(road, number, city_src)
        # Floors extract from the raw fields before any stripping: the
        # tails below drop the floor text ("7 A (3. kerros)"), while the
        # number survives as addr:floor. Reads the pre-road_base road so
        # a comma part carrying the floor is never missed.
        floor = self._extract_floor(number, road or "")
        if road and "," in road:
            road = self._road_base(road)
        if road and "/" in road:
            # Corner buildings name two streets; no single postal address.
            self._count("address/cross")
            item["street_address"] = self._strip_addr_base(road) or road
        elif road:
            core, units = self._number_parts(number)
            raw = self._strip_addr_base(f"{road} {core}".strip() if core else road)
            if not raw:
                pass
            elif not re.search(r"\d", raw):
                self._route_placeless(item, raw)
            elif parsed := self._split_addr_tokens(raw.split()):
                addr_street, house, unit = parsed
                fixed = re.sub(r"[A-Za-z]$", lambda m: m.group(0).lower(), house)
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
                    # 4): postcodes are never units.
                    dropped = [u for u in units if u == postcode]
                    if dropped:
                        self._count("address/postcode_in_unit", len(dropped))
                    units = [u for u in units if u != postcode]
                if units:
                    item["extras"]["addr:unit"] = " ".join(units)
            else:
                self._count("address/unparsed")
                item["street_address"] = raw
                if units:
                    item["extras"]["addr:unit"] = " ".join(units)
        if floor is not None:
            # Local floor numbering survives as addr:floor, never level.
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
            located = located[0].upper() + located[1:]
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
        if city_src and located and located.casefold() == city_src.strip().casefold():
            # A venue duplicating the municipality is not a venue.
            self._count("name/located_is_city")
            located = None
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
        slash_tail = None
        if " / " in signed and len(signed.split(" / ")) == 2:
            candidate = signed.rsplit(" / ", 1)[1].strip()
            if candidate and re.search(self.OPERATOR_END_RE, candidate, flags=re.IGNORECASE):
                slash_tail = candidate
        if slash_tail is not None:
            # Explicit operator companies/associations in the signed name
            # ("Imatra Bowling Center / Imatran keilahalli Oy") name the
            # operator; the tail is never a located venue.
            located = None
            item["operator"] = slash_tail
            self._count("operator/slash_tail")
            is_company = bool(re.search(r"\b(oy|ab)\.?$", slash_tail, flags=re.IGNORECASE))
            private_org = self._is_private_org(slash_tail)
            if is_company or private_org:
                item["extras"]["operator:type"] = "private"
            if private_org and not is_company and self._tag(item, "office") == "government":
                self._count("operator/office_demoted")
                item["extras"]["office"] = "association"
        if city_src:
            city_match = re.match(re.escape(city_src.strip()) + r"\s+[–—-]\s+(\S)", shown, flags=re.IGNORECASE)
        else:
            city_match = None
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
            shown = shown[0].upper() + shown[1:]
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
        # official_name* holds the unparsed signed form only: when nothing
        # was split or cleaned off, translations of the applied name are
        # name:sv/name:en instead (cf. Auroranportin yhteisöllinen asuminen).
        parsed = bool(official or cleaned != signed)
        if parsed:
            item["extras"]["official_name"] = signed
        self._apply_translations(item, names, shown, signed)

    def _apply_translations(self, item: Feature, names: dict[str, str], shown: str | None, signed: str | None) -> None:
        # Feed translations describe the applied service (Tykslab for
        # Laboratorio): always name:sv/name:en so renderers see them.
        # A copy of the signed form is not a translation
        # ("Steinergymnasiet (...)" in fi/sv/en alike). Rating
        # artifacts ("... 1*") strip off; bilingual pairs split.
        for lang in ("sv", "en"):
            translation = names.get(lang)
            if translation and translation != shown and translation != signed:
                cleaned_tr = re.sub(r"\s*\d+\*\s*$", "", translation).strip()
                cleaned_tr = re.sub(r",?\s*(?:[PN]\s*)?\d+\s*°.*$", "", cleaned_tr).strip()
                cleaned_tr = self._strip_fi_duplicates(cleaned_tr, shown, signed, item.get("located_in"))
                if "/" in cleaned_tr:
                    split_tr = self._split_bilingual(cleaned_tr, shown, signed, item.get("located_in"))
                    if split_tr is None:
                        continue
                    cleaned_tr = split_tr
                located = item.get("located_in")
                if cleaned_tr and cleaned_tr not in (shown, signed):
                    if not (located and cleaned_tr == located and located in (signed or "")):
                        # An untranslated copy of the Finnish-signed venue is
                        # not a translation ("Leikkipuisto Jakomäki" as en).
                        item["extras"][f"name:{lang}"] = cleaned_tr

    @staticmethod
    def _strip_fi_duplicates(cleaned_tr: str, shown: str | None, signed: str | None, located: str | None) -> str:
        # Exact Finnish duplicates ride along in feed translations
        # ("Korsverk (Ristikko)", "Aninkaisten koulu (Aninkainen
        # School) Gym A"): parenthesised or leading copies of the
        # applied/signed/venue name drop; the translated rest stays
        # verbatim (parens around translations are the feed's own).
        for form in dict.fromkeys([s for s in (shown, signed, located) if s]):
            cleaned_tr = re.sub(r"\s*\(" + re.escape(form) + r"\)", "", cleaned_tr).strip()
            if " / " not in cleaned_tr:
                head, sep, rest = cleaned_tr.partition(form)
                if sep and not head.strip() and rest and not rest.strip()[0].isalnum():
                    # Leading duplicate ("Aninkaisten koulu (...) Gym A"):
                    # the venue repeats the split-off Finnish name.
                    cleaned_tr = rest.strip(" ,–—-/")
        if located and "," in cleaned_tr and "," in (signed or ""):
            # Trailing comma tails duplicating the located venue
            # ("Daghemskök, Päiväkoti Jollas", "Skolrestaurang, Pasilan
            # peruskoulu"): positional match against the signed form, so
            # translated host copies ("Daycare Jollas") drop too. Stranded
            # comma-fragments in the shown name mark a mis-split: skip.
            fi_segs = [s.strip() for s in (signed or "").split(",")]
            tr_segs = [s.strip() for s in cleaned_tr.split(",")]
            if (
                len(fi_segs) == len(tr_segs)
                and len(tr_segs) >= 2
                and not re.search(r",\s*[A-ZÅÄÖ][a-zåäö-]+\s*$", shown or "")
            ):
                kept = [t for t, f in zip(tr_segs, fi_segs) if f != located]
                if kept and len(kept) < len(tr_segs):
                    cleaned_tr = ", ".join(kept)
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
        rest = []
        for i, s in enumerate(parts):
            if s in (shown, signed):
                continue
            if s.endswith("...") and len(s) > 6:
                base = s[:-3].strip().casefold()
                if any((form or "").strip().casefold().startswith(base) for form in (shown, signed)):
                    continue
            if positional:
                counterpart = fi_parts[i]
                if located and (counterpart == located or counterpart.startswith(located + ",")):
                    continue
                if not located and counterpart != shown and counterpart in (signed or ""):
                    continue
            rest.append(s)
        if not rest:
            return None
        if len(rest) < len(parts) and len(rest) == 1:
            return rest[0]
        return cleaned_tr

    def _apply_social_for(self, item: Feature, names: dict[str, str], name: str) -> None:
        # Elderly-targeted social facilities carry their clientele.
        if self._tag(item, "amenity") != "social_facility":
            return
        if "social_facility:for" in (item.get("extras") or {}):
            return
        cleaned_fi = self._clean_name(names.get("fi") or name)
        if any(
            stem in cleaned_fi.lower()
            for stem in ("ikäihmis", "ikäänty", "vanhus", "seniori", "eläkeläis", "pensionär")
        ):
            self._count("category/for_senior")
            item["extras"]["social_facility:for"] = "senior"

    def parse_channel(self, channel: dict) -> Feature | None:
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
            self._count("dropped/no_coords")
            return None

        item = Feature()
        item["ref"] = str(channel["id"])
        item["extras"]["ref:PTV"] = str(channel["id"])
        item["extras"]["source"] = "https://www.suomi.fi/palvelut/palvelupiste/" + str(channel["id"])
        modified = (channel.get("modified") or "").strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", modified):
            # The Suomi.fi "Päivitetty" date: record freshness per row.
            item["extras"]["check_date"] = modified[:10]
        city_src = self._city_src(street, channel, office)
        if office and self._post_city(office) != office.strip():
            # Station-village post offices file under their municipality.
            self._count("address/postoffice_station")
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
        # Category lands before naming so branch/operator demotion read it.
        self._apply_social_for(item, names, name)
        self._apply_naming(item, names, name, city_src)

        self._apply_address(item, street, postcode, city_src)
        item["lon"], item["lat"] = coords

        self._apply_contact(item, channel)

        hours = self._hours(channel, category)
        rendered = hours.as_opening_hours() if hasattr(hours, "as_opening_hours") else hours
        if hours and rendered:
            item["opening_hours"] = hours
        elif hours:
            # Objects rendering empty (closed-only sets) must never emit
            # an empty opening_hours tag.
            self._count("hours/empty_render")
        return item
