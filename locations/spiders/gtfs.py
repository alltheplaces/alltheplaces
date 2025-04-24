import copy
from io import BytesIO
from zipfile import ZipFile

from scrapy import Request
from scrapy.spiders import CSVFeedSpider
from scrapy.utils.iterators import csviter

from locations.categories import Extras, apply_category, apply_yes_no
from locations.items import Feature

BRAND_MAPPING = {
    "mdb-1": {
        "network": "Casco Bay Lines",
        "network:wikidata": "Q5048264",
        "operator": "Casco Bay Lines",
        "operator:wikidata": "Q5048264",
    },
    "mdb-3": {"network": "Barrie Transit", "network:wikidata": "Q4863566"},
    "mdb-11": {"network": "Amtrak", "network:wikidata": "Q23239"},
    "mdb-14": {
        # North County Transit District (NCTD)
        "network": "BREEZE",
        "network:wikidata": "Q7054956",
        "operator": "North County Transit District",
    },
    "mdb-15": {
        # Orange County Transportation Authority (OCTA)
        "network": "OC Bus",
        "network:wikidata": "Q6593059",
        "operator": "Orange County Transportation Authority",
        "operator:wikidata": "Q7099595",
    },
    "mdb-23": {
        # Lincoln County Transit (LCT)
        "network": "Lincoln County Transit",
        "network:wikidata": "Q107667781",
        "operator": "Lincoln County",
    },
    "mdb-25": {
        "network": "Eastern Sierra Transit",
        "network:wikidata": "Q5330465",
        "operator": "Eastern Sierra Transit",
    },
    "mdb-29": {
        # Los Angeles County Metropolitan Transportation Authority Bus
        "network": "Metro",
        "network:wikidata": "Q77610",
        "operator": "Los Angeles County Metropolitan Transportation Authority",
        "operator:wikidata": "Q3259702",
    },
    "mdb-30": {
        # LA Metro Rail
        "network": "Metro Rail",
        "network:wikidata": "Q1339558",
        "operator": "Los Angeles County Metropolitan Transportation Authority",
        "operator:wikidata": "Q3259702",
    },
    "mdb-34": {"network": "Torrance Transit", "network:wikidata": "Q7826932"},
    "mdb-37": {
        "network": "Big Blue Bus",
        "network:wikidata": "Q4905149",
        "operator": "City of Santa Monica",
        "operator:wikidata": "Q47164",
    },
    "mdb-38": {
        # Culver City Bus
        "network": "Culver CityBus",
        "network:wikidata": "Q5193719",
    },
    "mdb-43": {
        # San Luis Obispo Regional Transit Authority (SLORTA)
        "network": "RTA",
        "network:wikidata": "Q16984346",
        "operator": "San Luis Obispo Regional Transit Authority",
    },
    "mdb-47": {"network": "Kern Transit", "network:wikidata": "Q6394141"},
    "mdb-53": {
        # Bay Area Rapid Transit (BART)
        "network": "BART",
        "network:wikidata": "Q610120",
        "operator": "San Francisco Bay Area Rapid Transit District",
        "operator:wikidata": "Q4873922",
    },
    "mdb-54": {"network": "Caltrain", "network:wikidata": "Q166817"},
    "mdb-56": {
        # Monterey-Salinas Transit (MST)
        "network": "MST",
        "network:wikidata": "Q16982191",
    },
    "mdb-57": {
        # Santa Clara Valley Transportation Authority (VTA)
        "network": "VTA",
        "network:wikidata": "Q1456861",
    },
    "mdb-59": {
        # Stanford Marguerite Shuttle (SMS)
        "network": "Marguerite",
        "network:wikidata": "Q7598772",
        "operator": "Stanford Transportation",
        "operator:wikidata": "Q107966493",
    },
    "mdb-67": {
        # Golden Gate Transit
        "network": "GGT",
        "network:wikidata": "Q525895",
    },
    "mdb-71": {"network": "Marin Transit", "network:wikidata": "Q6763758"},
    "mdb-75": {"network": "El Dorado Transit", "network:wikidata": "Q5351201", "operator": "El Dorado Transit"},
    "mdb-78": {"network": "WestCAT", "network:wikidata": "Q7984179"},
    "mdb-79": {"network": "Yuba-Sutter Transit", "network:wikidata": "Q8060099"},
    "mdb-80": {
        # SolTrans
        "network": "SolTrans",
        "network:wikidata": "Q16984743",
    },
    "mdb-82": {"network": "Unitrans", "network:wikidata": "Q7893703"},
    "mdb-89": {
        "network": "Stageline",
        "network:wikidata": "Q130391671",
        "operator": "Clovis Transit",
        "operator:wikidata": "Q113396103",
    },
    "mdb-90": {
        # Fresno Area Express (FAX)
        "network": "FAX",
        "network:wikidata": "Q5503159",
    },
    "mdb-96": {
        "network": "Metrolink",
        "network:wikidata": "Q766647",
        "operator": "Southern California Regional Rail Authority",
    },
    "mdb-97": {
        # OmniTrans
        "network": "Omnitrans",
        "network:wikidata": "Q7090404",
    },
    "mdb-98": {"network": "RTA", "network:wikidata": "Q7338635", "operator": "Riverside Transit Agency"},
    "mdb-100": {
        # Anaheim Resort Transportation (ART)
        "network": "Anaheim Resort Transit",
        "network:wikidata": "Q4750893",
        "operator": "Transdev",
    },
    "mdb-101": {"network": "Foothill Transit", "network:wikidata": "Q5466493"},
    "mdb-108": {"network": "SunLine Transit Agency", "network:wikidata": "Q7638150"},
    "mdb-111": {
        # SunTran Utah
        "network": "SunTran",
        "network:wikidata": "Q19878145",
    },
    "mdb-121": {
        # Josephine County Transit (JCT)
        "network": "Josephine Community Transit",
        "network:wikidata": "Q107899789",
        "operator": "Josephine County",
    },
    "mdb-122": {
        # Rogue Valley Transportation District (RVTD)
        "network": "RVTD",
        "network:wikidata": "Q7359553",
        "operator": "Rogue Valley Transportation District",
    },
    "mdb-123": {
        "network": "UTrans",
        "network:wikidata": "Q107900150",
        "operator": "Umpqua Public Transportation District",
    },
    "mdb-126": {
        # Benton Area Transportation
        "network": "Benton Area Transit",
        "network:wikidata": "Q107667956",
        "operator": "Benton County",
    },
    "mdb-128": {"network": "Cherriots", "network:wikidata": "Q7404020", "operator": "Salem Area Mass Transit District"},
    "mdb-131": {
        # Lane Transit District (LTD)
        "network": "LTD",
        "network:wikidata": "Q6485453",
        "operator": "Lane Transit District",
    },
    "mdb-142": {
        # Valley Regional Transit
        "network": "VRT",
        "network:wikidata": "Q7912187",
    },
    "mdb-147": {
        # Valley Metro (VM)
        "network": "Valley Metro",
        "network:wikidata": "Q3553869",
    },
    "mdb-148": {"network": "Sun Metro", "network:wikidata": "Q7638408"},
    "mdb-151": {
        # Denton County Transportation Authority (DCTA)
        "network": "Denton County Transportation Authority",
        "network:wikidata": "Q5259601",
    },
    "mdb-152": {
        # Dallas Area Rapid Transit (DART)
        "network": "DART",
        "network:wikidata": "Q380660",
    },
    "mdb-161": {
        # Grand Valley Transit
        "network": "GVT",
        "network:wikidata": "Q5595228",
    },
    "mdb-166": {"network": "ABQ RIDE", "network:wikidata": "Q580832"},
    "mdb-170": {
        # Utah Transit Authority (UTA)
        "network": "UTA",
        "network:wikidata": "Q7902494",
    },
    "mdb-178": {
        # Regional Transportation District (RTD)
        "network": "RTD",
        "network:wikidata": "Q7309183",
    },
    "mdb-187": {
        # Kansas City Area Transportation Authority (KCATA)
        "network": "KCATA",
        "network:wikidata": "Q6364652",
    },
    "mdb-190": {
        # Metro St. Louis
        "network": "MetroBus",
        "network:wikidata": "Q6824411",
        "operator": "Metro Transit",
        "operator:wikidata": "Q4902339",
    },
    "mdb-206": {
        # Minnesota Valley Transit Authority (MVTA)
        "network": "MVTA",
        "network:wikidata": "Q6868609",
    },
    "mdb-250": {"network": "YCTA", "network:wikidata": "Q60770365", "operator": "Yamhill County Transit Area"},
    "mdb-252": {
        # Canby Area Transit (CAT)
        "network": "CAT",
        "network:wikidata": "Q5031301",
        "operator": "City of Canby",
    },
    "mdb-259": {
        # RiverCities Transit (RCT)
        "network": "RiverCities Transit",
        "network:wikidata": "Q28451877",
        "operator": "RiverCities Transit",
    },
    "mdb-260": {
        # Columbia Area Transit (CAT)
        "network": "CAT",
        "network:wikidata": "Q96375303",
        "operator": "Hood River County Transportation District",
    },
    "mdb-261": {
        # Sandy Area Metro (SAM)
        "network": "Sandy Area Metro",
        "network:wikidata": "Q107901414",
        "operator": "City of Sandy",
        "operator:wikidata": "Q2416599",
    },
    "mdb-262": {"network": "Skamania County Transit", "network:wikidata": "Q108172377", "operator": "Skamania County"},
    "mdb-263": {"network": "Grays Harbor Transit", "network:wikidata": "Q25000402", "operator": "Grays Harbor Transit"},
    "mdb-264": {
        # Mason Transit Authority
        "network": "Mason Transit",
        "network:wikidata": "Q20712385",
    },
    "mdb-265": {"network": "Pierce Transit", "network:wikidata": "Q7191834"},
    "mdb-266": {"network": "Intercity Transit", "network:wikidata": "Q2493414"},
    "mdb-268": {
        "network": "Sound Transit Express",
        "network:wikidata": "Q7564730",
        "operator": "Sound Transit",
        "operator:wikidata": "Q3965367",
    },
    "mdb-272": {
        # Kayak Transit (CTUIR)
        "network": "Kayak Public Transit",
        "network:wikidata": "Q107901212",
        "operator": "Confederated Tribes of the Umatilla Indian Reservation",
    },
    "mdb-275": {"network": "Link Transit", "network:wikidata": "Q25000891"},
    "mdb-279": {
        # Clallam Transit System
        "network": "Clallam Transit",
        "network:wikidata": "Q5125418",
    },
    "mdb-280": {"network": "Island Transit", "network:wikidata": "Q16980701"},
    "mdb-283": {"network": "Washington State Ferries", "network:wikidata": "Q3500373"},
    "mdb-284": {"network": "Whatcom Transportation Authority", "network:wikidata": "Q7991690"},
    "mdb-287": {
        # Community Transit (CT)
        "network": "Community Transit",
        "network:wikidata": "Q5154898",
    },
    "mdb-288": {"network": "Everett Transit", "network:wikidata": "Q5417075"},
    "mdb-290": {
        # Spokane Transit Authority (STA)
        "network": "STA",
        "network:wikidata": "Q7578886",
        "operator": "Spokane Transit Authority",
    },
    "mdb-301": {
        # Duluth Transit
        "network": "Duluth Transit Authority",
        "network:wikidata": "Q16967413",
    },
    "mdb-325": {
        # Hillsborough Area Regional Transit (HART)
        "network": "HART",
        "network:wikidata": "Q5763656",
    },
    "mdb-326": {
        # Pinellas Suncoast Transit Authority (PSTA)
        "network": "PSTA",
        "network:wikidata": "Q7195535",
    },
    "mdb-330": {
        # Broward County Transit
        "network": "BCT",
        "network:wikidata": "Q4975895",
    },
    "mdb-331": {
        # Miami-Dade Transit
        "network": "MDT",
        "network:wikidata": "Q6317384",
    },
    "mdb-332": {"network": "Palm Tran", "network:wikidata": "Q7128083"},
    "mdb-338": {
        # Montgomery Transit
        "network": "Montgomery Area Transit System",
        "network:wikidata": "Q6905645",
    },
    "mdb-346": {
        # Jacksonville Transportation Authority (JTA)
        "network": "JTA",
        "network:wikidata": "Q15051623",
        "operator": "Jacksonville Transportation Authority",
    },
    "mdb-352": {
        # Charleston Area Regional Transportation Authority (CARTA)
        "network": "CARTA",
        "network:wikidata": "Q5084103",
        "operator": "Charleston Area Regional Transportation Authority",
    },
    "mdb-364": {
        # Transit Authority of River City (TARC)
        "network": "TARC",
        "network:wikidata": "Q3537637",
        "operator": "Transit Authority of River City",
    },
    "mdb-366": {
        # Southwest Ohio Regional Transit Authority (SORTA Metro)
        "network": "SORTA",
        "network:wikidata": "Q107710058",
        "operator": "Southwest Ohio Regional Transit Authority",
        "operator:wikidata": "Q7571329",
    },
    "mdb-368": {
        # Metropolitan Atlanta Rapid Transit Authority (MARTA)
        "network": "MARTA",
        "network:wikidata": "Q1423792",
    },
    "mdb-377": {"network": "GoDurham", "network:wikidata": "Q5316462"},
    "mdb-381": {
        # Greater Lynchburg Transit Co.
        "network": "Greater Lynchburg Transit Company",
        "network:wikidata": "Q5600625",
    },
    "mdb-388": {
        # Champaign Urbana Mass Transit District (MTD)
        "network": "MTD",
        "network:wikidata": "Q5069909",
    },
    "mdb-389": {
        # Chicago Transit Authority (CTA)
        "network": "CTA",
        "network:wikidata": "Q117309",
        "operator": "Chicago Transit Authority",
    },
    "mdb-396": {
        # Waukesha Metro Transit
        "network": "Waukesha Metro",
        "network:wikidata": "Q7975163",
    },
    "mdb-400": {"network": "The Rapid", "network:wikidata": "Q14716158", "operator": "Interurban Transit Partnership"},
    "mdb-402": {
        # Capital Area Transportation Authority (CATA)
        "network": "CATA",
        "network:wikidata": "Q5035474",
        "operator": "Capital Area Transportation Authority",
    },
    "mdb-404": {
        # Central Ohio Transit Authority (COTA)
        "network": "COTA",
        "network:wikidata": "Q5061543",
    },
    "mdb-406": {
        "network": "RTA",
        "network:wikidata": "Q1544412",
        "operator": "Greater Cleveland Regional Transit Authority",
    },
    "mdb-414": {
        # Suburban Mobility Authority for Regional Transit (SMART)
        "network": "SMART",
        "network:wikidata": "Q7632360",
    },
    "mdb-415": {
        # Ann Arbor Area Transportation Authority (TheRide)
        "network": "AAATA",
        "network:wikidata": "Q4766233",
    },
    "mdb-418": {
        # Greater Attleboro Taunton Regional Transit Authority (GATRA)
        "network": "GATRA",
        "network:wikidata": "Q5600434",
    },
    "mdb-420": {
        # Martha's Vineyard Transit Authority
        "network": "VTA",
        "network:wikidata": "Q20715059",
    },
    "mdb-421": {
        # Southeastern Regional Transit Authority (SRTA)
        "network": "SRTA",
        "network:wikidata": "Q7569500",
    },
    "mdb-422": {
        # Brockton Area Transit Authority (BAT)
        "network": "BAT",
        "network:wikidata": "Q4972867",
        "operator": "Brockton Area Transit Authority",
    },
    "mdb-432": {
        # Worcester Regional Transit Authority (WRTA)
        "network": "WRTA",
        "network:wikidata": "Q8034217",
        "operator": "Worcester Regional Transit Authority",
    },
    "mdb-433": {
        # Montachusett Regional Transit Authority (MART)
        "network": "MART",
        "network:wikidata": "Q6903133",
    },
    "mdb-437": {
        # Massachusetts Bay Transportation Authority (MBTA)
        "network": "MBTA",
        "network:wikidata": "Q171985",
    },
    "mdb-439": {
        # MetroWest Regional Transit Authority (MWRTA)
        "network": "MWRTA",
        "network:wikidata": "Q6824447",
    },
    "mdb-444": {
        # Lowell Regional Transit Authority (LRTA)
        "network": "LRTA",
        "network:wikidata": "Q2078562",
    },
    "mdb-447": {
        # Cape Ann Transportation Authority (CATA)
        "network": "CATA",
        "network:wikidata": "Q5034570",
        "operator": "Cape Ann Transportation Authority",
    },
    "mdb-464": {
        # Detroit Department of Transportation (DDOT)
        "network": "DDOT",
        "network:wikidata": "Q5265906",
    },
    "mdb-466": {
        # Maryland Transit Administration Local Bus
        "network": "MTA Commuter Bus",
        "network:wikidata": "Q111770225",
        "operator": "Maryland Transit Administration",
        "operator:wikidata": "Q1863801",
    },
    "mdb-468": {
        # Maryland Transit Administration MARC Train
        "network": "MARC",
        "network:wikidata": "Q6714458",
        "operator": "Maryland Transit Administration",
        "operator:wikidata": "Q1863801",
    },
    "mdb-469": {
        # Maryland Transit Administration Light Rail
        "network": "Baltimore Light RailLink",
        "network:wikidata": "Q3333820",
        "operator": "Maryland Transit Administration",
        "operator:wikidata": "Q1863801",
    },
    "mdb-473": {
        # Hampton Roads Transit (HRT)
        "network": "HRT",
        "network:wikidata": "Q5646293",
    },
    "mdb-483": {"network": "Fairfax Connector", "network:wikidata": "Q5430155"},
    "mdb-485": {"network": "Arlington Transit", "network:wikidata": "Q4792406"},
    "mdb-502": {
        # Southeastern Pennsylvania Transportation Authority (SEPTA) Bus
        "network": "SEPTA",
        "network:wikidata": "Q2037863",
    },
    "mdb-503": {
        # Southeastern Pennsylvania Transportation Authority (SEPTA) Rail
        "network": "SEPTA",
        "network:wikidata": "Q2037863",
    },
    "mdb-505": {
        # PATCO Speedline
        "network": "PATCO",
        "network:wikidata": "Q2043730",
        "operator": "Delaware River Port Authority",
        "operator:wikidata": "Q948591",
    },
    "mdb-515": {
        # NYC Ferry
        "network": "NY Waterway",
        "network:wikidata": "Q6956135",
    },
    "mdb-517": {
        # Port Authority Trans-Hudson (PATH)
        "network": "PATH",
        "network:wikidata": "Q1055811",
        "operator": "Port Authority of New York and New Jersey",
        "operator:wikidata": "Q908666",
    },
    "mdb-518": {
        "network": "Staten Island Ferry",
        "network:wikidata": "Q1048582",
        "operator": "NYCDOT",
        "operator:wikidata": "Q1058767",
    },
    "mdb-521": {
        # Nassau Inter-County Express (NICE Bus)
        "network": "Nassau Inter-County Express",
        "network:wikidata": "Q6967576",
        "operator": "Transdev",
        "operator:wikidata": "Q104185516",
    },
    "mdb-530": {
        # Greater Bridgeport Transit
        "network": "GBT",
        "network:wikidata": "Q5600471",
    },
    "mdb-533": {
        # Rochester-Genesee Regional Transportation Authority (RGRTA)
        "network": "RTS Livingston",
        "network:wikidata": "Q128019453",
        "operator": "Rochester-Genesee Regional Transportation Authority",
        "operator:wikidata": "Q7353936",
    },
    "mdb-534": {
        # Centro
        "network": "Centro Rome",
        "network:wikidata": "Q130302467",
        "operator": "Central New York Regional Transportation Authority",
        "operator:wikidata": "Q5061513",
    },
    "mdb-535": {
        # Tompkins Consolidated Area Transit Inc
        "network": "TCAT",
        "network:wikidata": "Q7820360",
        "operator": "Tompkins Consolidated Area Transit",
    },
    "mdb-537": {
        # Berkshire Regional Transit Authority (BRTA)
        "network": "BRTA",
        "network:wikidata": "Q20708878",
    },
    "mdb-538": {
        # Capital District Transportation Authority (CDTA)
        "network": "Capital District Transportation Authority",
        "network:wikidata": "Q5035551",
    },
    "mdb-548": {"network": "Suffolk County Transit", "network:wikidata": "Q7634561"},
    "mdb-553": {
        # Connecticut Transit
        "network": "CTtransit",
        "network:wikidata": "Q1652279",
    },
    "mdb-580": {
        "network": "Mount Adams Transportation Service",
        "network:wikidata": "Q108172416",
        "operator": "Klickitat County",
    },
    "mdb-585": {
        # South Shore Line
        "network": "NICTD",
        "network:wikidata": "Q31313",
        "operator": "NICTD",
        "operator:wikidata": "Q31313",
    },
    "mdb-591": {"network": "Petersburg Area Transit", "network:wikidata": "Q7178176"},
    "mdb-618": {
        # Harbor Connector
        "network": "Baltimore Harbor Connector",
        "network:wikidata": "Q111771534",
        "operator": "Baltimore City Department of Transportation",
        "operator:wikidata": "Q28901255",
    },
    "mdb-624": {
        "network": "RIPTA",
        "network:wikidata": "Q7320944",
        "operator": "Rhode Island Public Transit Authority",
    },
    "mdb-631": {"network": "AT", "network:wikidata": "Q17084449", "operator": "Advance Transit"},
    "mdb-656": {"network": "Kicéo", "network:wikidata": "Q3537959", "operator": "Transdev GMVA Mobilités"},
    "mdb-657": {
        # Public Transport Victoria (PTV)
        "network": "PTV",
        "network:wikidata": "Q7257648",
    },
    "mdb-659": {
        # Région Bourgogne-Franche-Comté
        "network": "TER Bourgogne-Franche-Comté",
        "network:wikidata": "Q43082620",
        "operator": "SNCF",
        "operator:wikidata": "Q13646",
    },
    "mdb-660": {"network": "Adelaide Metro", "network:wikidata": "Q4681753"},
    "mdb-665": {
        # MetroTas Hobart
        "network": "Metro Tasmania",
        "network:wikidata": "Q6824728",
        "operator": "Metro Tasmania",
    },
    "mdb-681": {
        # MetroTas Burnie
        "network": "Metro Tasmania",
        "network:wikidata": "Q6824728",
        "operator": "Metro Tasmania",
    },
    "mdb-682": {
        # MetroTas Launceston
        "network": "Metro Tasmania",
        "network:wikidata": "Q6824728",
        "operator": "Metro Tasmania",
    },
    "mdb-684": {"network": "De Lijn", "network:wikidata": "Q614819", "operator": "De Lijn"},
    "mdb-689": {
        # Whitehorse Transit
        "network": "City of Whitehorse Transit",
        "network:wikidata": "Q7996083",
    },
    "mdb-690": {"network": "BC Ferries", "network:wikidata": "Q795723"},
    "mdb-712": {
        # Calgary Transit
        "network": "CT",
        "network:wikidata": "Q143630",
    },
    "mdb-714": {
        # Edmonton Transit System
        "network": "ETS",
        "network:wikidata": "Q3048058",
    },
    "mdb-717": {"network": "Winnipeg Transit", "network:wikidata": "Q3569372"},
    "mdb-721": {"network": "Grand River Transit", "network:wikidata": "Q3459117"},
    "mdb-724": {"network": "Burlington Transit", "network:wikidata": "Q2928517"},
    "mdb-725": {"network": "Oakville Transit", "network:wikidata": "Q7074262"},
    "mdb-726": {"network": "Durham Region Transit", "network:wikidata": "Q5316548"},
    "mdb-728": {"network": "York Region Transit", "network:wikidata": "Q5182500"},
    "mdb-730": {"network": "MiWay", "network:wikidata": "Q1526431"},
    "mdb-732": {
        "network": "Toronto subway",
        "network:wikidata": "Q20379",
        "operator": "Toronto Transit Commission",
        "operator:wikidata": "Q17978",
    },
    "mdb-733": {"network": "Kingston Transit", "network:wikidata": "Q6413628"},
    "mdb-734": {"network": "Halifax Transit", "network:wikidata": "Q14875719"},
    "mdb-735": {
        # VIA Rail Canada
        "network": "VIA Rail",
        "network:wikidata": "Q876720",
    },
    "mdb-736": {"network": "Thunder Bay Transit", "network:wikidata": "Q7798949"},
    "mdb-740": {
        # Société de transport de l'Outaouais
        "network": "STO",
        "network:wikidata": "Q3488034",
    },
    "mdb-741": {
        # Exo Sorel-Varennes
        "network": "exo-Sorel-Varennes",
        "network:wikidata": "Q5011938",
    },
    "mdb-742": {
        # Exo Sud-ouest
        "network": "exo-Sud-Ouest",
        "network:wikidata": "Q2994092",
    },
    "mdb-743": {
        # Exo La Presqu'île
        "network": "exo-La Presqu'île",
        "network:wikidata": "Q4801810",
    },
    "mdb-744": {
        # Exo Laurentides
        "network": "exo-Laurentides",
        "network:wikidata": "Q2994089",
    },
    "mdb-748": {
        # Exo Trains
        "network": "exo",
        "network:wikidata": "Q392496",
    },
    "mdb-749": {
        # Société de transport de Laval
        "network": "STL",
        "network:wikidata": "Q3488029",
    },
    "mdb-750": {
        # Exo Chambly-Richelieu-Carignan
        "network": "exo-Chambly-Richelieu-Carignan",
        "network:wikidata": "Q5011933",
    },
    "mdb-752": {
        # Exo Vallée du Richelieu
        "network": "exo-Vallée du Richelieu",
        "network:wikidata": "Q2994091",
    },
    "mdb-754": {
        # Terrebonne-Mascouche
        "network": "exo-Terrebonne-Mascouche",
        "network:wikidata": "Q55596813",
    },
    "mdb-755": {
        # Exo L'Assomption
        "network": "exo-L'Assomption",
        "network:wikidata": "Q55596812",
    },
    "mdb-757": {"network": "RTC", "network:wikidata": "Q3456768", "operator": "Réseau de transport de la Capitale"},
    "mdb-759": {"network": "Milton Transit", "network:wikidata": "Q6861499"},
    "mdb-763": {"network": "STLévis", "network:wikidata": "Q3488027", "operator": "Société de transport de Lévis"},
    "mdb-778": {"network": "Verkehrsverbund Rhein-Sieg", "network:wikidata": "Q896041"},
    "mdb-779": {
        # Münchner Verkehrs- und Tarifverbund GmbH (MVV)
        "network": "Münchner Verkehrs- und Tarifverbund",
        "network:wikidata": "Q259000",
    },
    "mdb-782": {"network": "Verkehrsverbund Berlin-Brandenburg", "network:wikidata": "Q315451"},
    "mdb-793": {
        # Empresa Municipal de Transportes de Madrid (EMT Madrid)
        "network": "Empresa Municipal de Transportes de Madrid",
        "network:wikidata": "Q1094755",
        "operator": "Empresa Municipal de Transportes de Madrid",
        "operator:wikidata": "Q1094755",
    },
    "mdb-794": {"network": "Metro de Madrid", "network:wikidata": "Q191987"},
    "mdb-795": {
        # EMT Valencia
        "network": "EMT",
        "network:wikidata": "Q11007711",
    },
    "mdb-800": {
        "network": "Public Oregon Intercity Transit",
        "network:wikidata": "Q19877418",
        "operator": "Oregon Department of Transportation",
        "operator:wikidata": "Q4413096",
    },
    "mdb-812": {"network": "Santa Clarita Transit", "network:wikidata": "Q5123908"},
    "mdb-813": {"network": "Santa Ynez Valley Transit", "network:wikidata": "Q101538719"},
    "mdb-815": {
        # Sonoma-Marin Area Rail Transit (SMART)
        "network": "SMART",
        "network:wikidata": "Q7562166",
        "operator": "Sonoma-Marin Area Rail Transit",
        "operator:wikidata": "Q7562166",
    },
    "mdb-840": {
        # TRENITALIA S.p.A.
        "network": "Trenitalia",
        "network:wikidata": "Q286650",
        "operator": "Trenitalia",
        "operator:wikidata": "Q286650",
    },
    "mdb-844": {
        # Transports de l'agglomération de Montpellier (TAM)
        "network": "TaM",
        "network:wikidata": "Q3537922",
    },
    "mdb-853": {
        # FlixBus
        "network": "Flixbus",
        "network:wikidata": "Q15712258",
    },
    "mdb-857": {
        # Augsburger Verkehrs- und Tarifverbund (AVV)
        "network": "Augsburger Verkehrs- und Tarifverbund",
        "network:wikidata": "Q760574",
    },
    "mdb-858": {
        # Ver­kehrs­ver­bund Groß­raum Nürn­berg (VGN)
        "network": "Verkehrsverbund Großraum Nürnberg",
        "network:wikidata": "Q2516463",
    },
    "mdb-883": {
        "network": "SCTD",
        "network:wikidata": "Q7566833",
        "operator": "South Clackamas Transportation District",
    },
    "mdb-888": {
        # Aix en Bus
        "network": "Aix-en-Bus",
        "network:wikidata": "Q3537934",
    },
    "mdb-923": {"network": "CyRide", "network:wikidata": "Q5197282"},
    "mdb-978": {
        # Trentino Trasporti SpA (TT)
        "network": "Servizio Extraurbano",
        "operator": "Trentino Trasporti",
        "operator:wikidata": "Q3998389",
    },
    "mdb-983": {
        # Otago Regional Council (ORC)
        "network": "Otago Regional Council",
        "network:wikidata": "Q7108351",
    },
    "mdb-988": {"network": "Ulysse", "network:wikidata": "Q16674417"},
    "mdb-1009": {
        # ZDMiKP w Bydgoszczy
        "network": "ZDMiKP Bydgoszcz",
        "network:wikidata": "Q16618278",
    },
    "mdb-1011": {
        # Koleje Mazowieckie (KM)
        "network": "Koleje Mazowieckie",
        "network:wikidata": "Q847966",
    },
    "mdb-1024": {"network": "Tisséo", "network:wikidata": "Q3529461"},
    "mdb-1029": {
        # Auckland Transport
        "network": "AT",
        "network:wikidata": "Q4819567",
    },
    "mdb-1032": {
        "network": "Carris",
        "network:wikidata": "Q1045108",
        "operator": "Carris",
        "operator:wikidata": "Q1045108",
    },
    "mdb-1052": {
        # TRENITALIA
        "network": "Trenitalia",
        "network:wikidata": "Q286650",
        "operator": "Trenitalia",
        "operator:wikidata": "Q286650",
    },
    "mdb-1054": {
        # MetroValencia
        "network": "Metrovalencia",
        "network:wikidata": "Q511171",
        "operator": "Ferrocarrils de la Generalitat Valenciana",
        "operator:wikidata": "Q750832",
    },
    "mdb-1056": {"network": "Ciotabus", "network:wikidata": "Q16539909"},
    "mdb-1066": {
        # Società Gestione Multipla (SGM)
        "network": "SGM",
        "network:wikidata": "Q63515780",
    },
    "mdb-1071": {"network": "BayBus", "network:wikidata": "Q112189811"},
    "mdb-1085": {
        # Verkehrsverbund Pforzheim-Enzkreis (VPE)
        "network": "Verkehrsverbund Pforzheim-Enzkreis",
        "network:wikidata": "Q2516474",
    },
    "mdb-1111": {
        # Codiac Transport
        "network": "Codiac Transpo",
        "network:wikidata": "Q2981688",
    },
    "mdb-1116": {"network": "Ginko", "network:wikidata": "Q3106780", "operator": "Keolis Besançon"},
    "mdb-1132": {"network": "Metlink", "network:wikidata": "Q7258026"},
    "mdb-1173": {"network": "Verkehrsverbund Rhein-Neckar", "network:wikidata": "Q1553051"},
    "mdb-1198": {
        # Long Beach Transit (LBT)
        "network": "Long Beach Transit",
        "network:wikidata": "Q6672372",
    },
    "mdb-1205": {
        # SNCF TER timetable
        "network": "TER Bretagne",
        "network:wikidata": "Q975369",
        "operator": "SNCF",
        "operator:wikidata": "Q13646",
    },
    "mdb-1232": {
        # Pueblo Transit Flex
        "network": "Pueblo Transit",
        "network:wikidata": "Q7258466",
    },
    "mdb-1246": {
        # Santa Barbara Metropolitan Transit District (MTD)
        "network": "Santa Barbara MTD",
        "network:wikidata": "Q7419232",
    },
    "mdb-1304": {"network": "Kitsap Transit", "network:wikidata": "Q6418321"},
    "mdb-1330": {"network": "King County Metro", "network:wikidata": "Q6411393"},
    "mdb-1331": {"network": "Washington State Ferries", "network:wikidata": "Q3500373"},
    "mdb-1820": {
        # Réseau Mistral
        "network": "Mistral",
        "network:wikidata": "Q3456576",
    },
    "mdb-1832": {
        # Železničná spoločnosť Slovensko, a.s.
        "network": "ZSSK",
        "network:wikidata": "Q837019",
        "operator": "ZSSK",
        "operator:wikidata": "Q393557",
    },
    "mdb-1837": {"network": "BreizhGo", "network:wikidata": "Q55595872"},
    "mdb-1846": {
        # Washington Metropolitan Area Transit Authority (WMATA) Bus
        "network": "WMATA Metrobus",
        "network:wikidata": "Q6824810",
        "operator": "Washington Metropolitan Area Transit Authority",
        "operator:wikidata": "Q7972051",
    },
    "mdb-1847": {
        # Washington Metropolitan Area Transit Authority (WMATA) Rail
        "network": "Washington Metro",
        "network:wikidata": "Q171221",
        "operator": "Washington Metropolitan Area Transit Authority",
        "operator:wikidata": "Q7972051",
    },
    "mdb-1877": {"network": "SURF", "network:wikidata": "Q56310007"},
    "mdb-1891": {"network": "T'MM", "network:wikidata": "Q3537813"},
    "mdb-1896": {"network": "Transavold", "network:wikidata": "Q3537389"},
    "mdb-1897": {"network": "REZO", "network:wikidata": "Q3537839"},
    "mdb-1898": {
        # Agglobus
        "network": "AggloBus",
        "network:wikidata": "Q3537943",
    },
    "mdb-1909": {"network": "Transjakarta", "network:wikidata": "Q1671143"},
    "mdb-1946": {
        # Nottingham City Transport
        "network": "NCT",
        "network:wikidata": "Q7063616",
    },
    "mdb-1948": {"network": "Plymouth Citybus", "network:wikidata": "Q7205782"},
    "mdb-1951": {"network": "Southern Vectis", "network:wikidata": "Q4049829"},
    "mdb-1955": {"network": "Unilink", "network:wikidata": "Q7884624"},
    "mdb-1956": {
        "network": "Warrington's Own Buses",
        "network:wikidata": "Q7000937",
        "operator": "Warrington's Own Buses",
        "operator:wikidata": "Q7000937",
    },
    "mdb-1974": {"network": "Tri Delta Transit", "network:wikidata": "Q7839840"},
    "mdb-1992": {"network": "Red Deer Transit", "network:wikidata": "Q7304013"},
    "mdb-1993": {
        # Go Transit
        "network": "GO Transit",
        "network:wikidata": "Q1357727",
        "operator": "Metrolinx",
        "operator:wikidata": "Q3307451",
    },
    "mdb-1999": {"network": "Beach Cities Transit", "network:wikidata": "Q4875696"},
    "mdb-2000": {
        # Red Rose Transit Authority (RRTA)
        "network": "RRTA",
        "network:wikidata": "Q7304963",
        "operator": "Red Rose Transit Authority",
    },
    "mdb-2001": {
        # Stark Area Regional Transit Authority (SARTA)
        "network": "SARTA",
        "network:wikidata": "Q7601948",
        "operator": "Stark Area Regional Transit Authority",
    },
    "mdb-2025": {
        # Mountain View Transportation Management Association (MVgo)
        "network": "MVgo",
        "network:wikidata": "Q110544414",
        "operator": "Mountain View Transportation Management Association",
        "operator:wikidata": "Q110544427",
    },
    "mdb-2027": {"network": "Carris Metropolitana", "network:wikidata": "Q111611112"},
    "mdb-2064": {
        # Berks Area Regional Transportation Authority (BARTA)
        "network": "BARTA",
        "network:wikidata": "Q4892231",
    },
    "mdb-2066": {"network": "BT", "network:wikidata": "Q4928359", "operator": "Bloomington Transit"},
    "mdb-2068": {
        # Transit Authority of Northern Kentucky (TANK)
        "network": "TANK",
        "network:wikidata": "Q7834339",
    },
    "mdb-2069": {
        # Valley Transit (WI)
        "network": "VT",
        "network:wikidata": "Q7912245",
    },
    "mdb-2071": {
        # Akron Metro Regional Transit Authority (METRO)
        "network": "METRO RTA",
        "network:wikidata": "Q6715494",
    },
    "mdb-2079": {
        # Broome County Transit (B.C. Transit)
        "network": "Broome County Transit",
        "network:wikidata": "Q4975274",
        "operator": "Broome County Department of Public Transportation",
    },
    "mdb-2090": {"network": "MZDiK Radom", "network:wikidata": "Q11780285"},
    "mdb-2099": {
        # Tursib Sibiu
        "network": "Tursib",
        "network:wikidata": "Q1477885",
    },
    "mdb-2100": {
        # CT BUS Constanța
        "network": "CT Bus",
        "network:wikidata": "Q3928165",
    },
    "mdb-2115": {"network": "RAT Craiova", "network:wikidata": "Q25399056"},
    "mdb-2122": {"network": "Ben Franklin Transit", "network:wikidata": "Q4885675"},
    "mdb-2126": {
        # Société de transport de Montréal (STM)
        "network": "STM",
        "network:wikidata": "Q1817151",
    },
    "mdb-2127": {
        # Milwaukee County Transit System (MCTS)
        "network": "MCTS",
        "network:wikidata": "Q1935975",
    },
    "mdb-2131": {"network": "Saint John Transit", "network:wikidata": "Q7401471"},
    "mdb-2142": {
        # Exo Le Richelain / Roussillon
        "network": "exo-Le Richelain",
        "network:wikidata": "Q2994087",
    },
    "mdb-2155": {
        # Integrated Transit System of the South Moravian Region (IDS JMK)
        "network": "IDS JMK",
        "network:wikidata": "Q12020731",
    },
    "mdb-2201": {
        "network": "Montebello Bus Lines",
        "network:wikidata": "Q6905005",
        "operator": "City of Montebello",
        "operator:wikidata": "Q664503",
    },
    "mdb-2232": {"network": "Pueblo Transit", "network:wikidata": "Q7258466"},
    "mdb-2240": {"network": "Southeast Area Transit District", "network:wikidata": "Q7569291"},
    "mdb-2242": {
        # Norwalk Transit System (NTS)
        "network": "Norwalk Transit",
        "network:wikidata": "Q7060801",
    },
    "mdb-2254": {"network": "Bay Area Transportation Authority", "network:wikidata": "Q20710576"},
    "mdb-2264": {
        "network": "Rock Region Metro",
        "network:wikidata": "Q5060353",
        "operator": "Rock Region Metropolitan Transit Authority",
    },
    "mdb-2265": {
        # Charlotte Area Transit System (CATS)
        "network": "CATS",
        "network:wikidata": "Q5085831",
        "operator": "Charlotte Area Transit System",
    },
    "mdb-2267": {"network": "Connect Transit", "network:wikidata": "Q4928329"},
    "mdb-2269": {"network": "StarTran", "network:wikidata": "Q7600574"},
    "mdb-2270": {
        "network": "GTrans",
        "network:wikidata": "Q5522428",
        "operator": "City of Gardena",
        "operator:wikidata": "Q846409",
    },
    "mdb-2272": {
        # Santa Maria Area Transit
        "network": "Santa Maria Regional Transit",
        "network:wikidata": "Q7419673",
    },
    "mdb-2277": {"network": "GoCary", "network:wikidata": "Q5005923"},
    "mdb-2280": {
        # Regional Transportation District (RTD) Bustang
        "network": "RTD",
        "network:wikidata": "Q7309183",
        "operator": "Regional Transportation District",
    },
    "mdb-2293": {
        # Transfort Flex
        "network": "Transfort",
        "network:wikidata": "Q7834201",
    },
    "mdb-2309": {
        "network": "Grant Transit Authority",
        "network:wikidata": "Q28445738",
        "operator": "Grant Transit Authority",
    },
    "mdb-2313": {
        "network": "Jackson Transit Authority",
        "network:wikidata": "Q130387505",
        "operator": "Jackson Transit Authority",
    },
    "mdb-2321": {
        "network": "Megabus",
        "network:wikidata": "Q6808155",
        "operator": "Stagecoach Group",
        "operator:wikidata": "Q660261",
    },
    "mdb-2332": {
        # Shawnee Mass Transit District
        "network": "SMTD",
        "network:wikidata": "Q7580990",
        "operator": "Sangamon Mass Transit District",
    },
    "mdb-2347": {
        # Pace Bus
        "network": "Pace",
        "network:wikidata": "Q3360030",
        "operator": "Regional Transportation Authority",
        "operator:wikidata": "Q3423544",
    },
    "mdb-2351": {
        # Regional Transportation Commission of Southern Nevada (RTC)
        "network": "RTC",
        "network:wikidata": "Q7309181",
        "operator": "Regional Transportation Commission of Southern Nevada",
    },
    "mdb-2354": {
        # SunTran
        "network": "Sun Tran",
        "network:wikidata": "Q7638551",
    },
    "mdb-2356": {"network": "Mountain Metropolitan Transit", "network:wikidata": "Q6925119"},
    "mdb-2359": {
        # Transports Metropolitans de Barcelona (TMB) TMB
        "network": "TMB",
        "network:wikidata": "Q1778212",
    },
    "mdb-2360": {
        # Mitteldeutscher Verkehrsverbund GmbH (MDV)
        "network": "Mitteldeutscher Verkehrsverbund",
        "network:wikidata": "Q1742463",
    },
    "mdb-2363": {"network": "DMT", "network:wikidata": "Q115938980", "operator": "Danville Mass Transit"},
    "mdb-2373": {
        # AMAT Palermo S.P.A.
        "network": "AMAT",
        "network:wikidata": "Q3601014",
    },
    "mdb-2394": {
        # Yosemite Area Regional Transportation System (YARTS)
        "network": "YARTS",
        "network:wikidata": "Q8055918",
    },
    "mdb-2400": {
        # Empresa Municipal de Transportes de Fuenlabrada (EMTF)
        "network": "EMT Fuenlabrada",
        "network:wikidata": "Q5831722",
    },
    "mdb-2416": {
        # Pioneer Valley Transit Authority (PVTA)
        "network": "PVTA",
        "network:wikidata": "Q7196828",
    },
    "mdb-2426": {
        "network": "Xpress",
        "network:wikidata": "Q5514501",
        "operator": "Georgia Regional Transportation Authority",
    },
    "mdb-2434": {
        # Arlington Transit Flex
        "network": "Arlington Transit",
        "network:wikidata": "Q4792406",
    },
    "mdb-2441": {
        # Petersburg Area Transit Flex
        "network": "Petersburg Area Transit",
        "network:wikidata": "Q7178176",
    },
    "mdb-2457": {
        # Hyderabad Metro Rail Ltd.
        "network": "Hyderabad Metro",
        "network:wikidata": "Q646209",
    },
    "mdb-2460": {"network": "Fredericton Transit", "network:wikidata": "Q5499255"},
    "mdb-2462": {
        # BC Transit (Hazelton)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "mdb-2463": {
        # BC Transit (Quesnel)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "mdb-2464": {
        # BC Transit (Revelstoke)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "mdb-2471": {
        # BC Transit (Merritt)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "mdb-2472": {
        # BC Transit (Smithers)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "mdb-2473": {
        # BC Transit (Nanaimo)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "mdb-2515": {
        # BC Transit (Clearwater)
        "network": "BC Transit",
        "network:wikidata": "Q4179186",
    },
    "ntd-41": {
        # Alaska Railroad Corporation
        "network": "ARR",
        "network:wikidata": "Q1235460",
    },
    "ntd-10004": {"network": "BAT", "network:wikidata": "Q4972867", "operator": "Brockton Area Transit Authority"},
    "ntd-30054": {
        # Centre Area Transportation Authority (CATABUS)
        "network": "CATABUS",
        "network:wikidata": "Q5062227",
        "operator": "Centre Area Transportation Agency",
    },
    "ntd-40188": {
        # Virgin Island Transit (VITran)
        "network": "Virgin Islands Transit",
        "network:wikidata": "Q116925354",
    },
    "ntd-50090": {"network": "RCT", "network:wikidata": "Q7330624", "operator": "Richland County Transit"},
    "ntd-60032": {
        # New Orleans Regional Transit Authority (NORTA)
        "network": "RTA",
        "network:wikidata": "Q2138272",
        "operator": "New Orleans Regional Transit Authority",
    },
    "ntd-90091": {"network": "Visalia Transit", "network:wikidata": "Q110722964"},
    "ntd-90162": {"network": "Tri Delta Transit", "network:wikidata": "Q7839840"},
    "ntd-90208": {
        # Butte Regional Transit (B-Line)
        "network": "B-Line",
        "network:wikidata": "Q5002811",
        "operator": "Butte Regional Transit",
    },
    "ntd-90237": {
        # The Kauai Bus
        "network": "The Kauaʻi Bus",
        "network:wikidata": "Q7744015",
        "operator": "County of Kauaʻi",
    },
    "tld-89": {
        # Chapel Hill Transit
        "network": "CHT",
        "network:wikidata": "Q5073024",
    },
    "tld-98": {"network": "GoDurham", "network:wikidata": "Q5316462"},
    "tld-170": {"network": "CET", "network:wikidata": "Q107900782", "operator": "Cascades East Transit"},
    "tld-217": {
        # VIA Metropolitan Transit
        "network": "VIA",
        "network:wikidata": "Q7906973",
    },
    "tld-223": {
        "network": "rabbittransit",
        "network:wikidata": "Q7278624",
        "operator": "Central Pennsylvania Transportation Authority",
    },
    "tld-288_1": {
        "network": "Charm City Circulator",
        "network:wikidata": "Q5086389",
        "operator": "Baltimore City Department of Transportation",
        "operator:wikidata": "Q28901255",
    },
    "tld-395": {"network": "Wichita Transit", "network:wikidata": "Q7998172"},
    "tld-401": {
        "network": "NFTA Metro",
        "network:wikidata": "Q15114900",
        "operator": "Niagara Frontier Transportation Authority",
    },
    "tld-408": {"network": "Guelph Transit", "network:wikidata": "Q5614797"},
    "tld-438": {"network": "Torrance Transit", "network:wikidata": "Q7826932"},
    "tld-461": {"network": "SunLine Transit Agency", "network:wikidata": "Q7638150"},
    "tld-471": {
        # Glendale Beeline
        "network": "Beeline",
        "network:wikidata": "Q5568346",
        "operator": "City of Glendale",
    },
    "tld-616": {"network": "Wexford Bus", "network:wikidata": "Q117196712"},
    "tld-635": {
        # Dublin Bus Nitelink
        "network": "Dublin Bus",
        "network:wikidata": "Q1263090",
    },
    "tld-637": {
        # Citylink
        "network": "Irish Citylink",
        "network:wikidata": "Q15712847",
    },
    "tld-651": {
        # FlixTrain (Europe)
        "network": "FlixTrain",
        "network:wikidata": "Q55499626",
        "operator": "FlixTrain",
        "operator:wikidata": "Q55499626",
    },
    "tld-715": {"network": "Fertagus", "network:wikidata": "Q1408210"},
    "tld-716": {
        # Metro de Lisboa (Metro)
        "network": "Metropolitano de Lisboa",
        "network:wikidata": "Q746032",
        "operator": "Metropolitano de Lisboa",
        "operator:wikidata": "Q746032",
    },
    "tld-752": {
        # Public Transport Victoria
        "network": "PTV",
        "network:wikidata": "Q7257648",
    },
    "tld-757_1": {
        "network": "FAST",
        "network:wikidata": "Q5439044",
        "operator": "Fayetteville Area System of Transit",
        "operator:wikidata": "Q5439044",
    },
    "tld-768_1": {"network": "Red Metropolitana de Movilidad", "network:wikidata": "Q954223"},
    "tld-820": {"network": "Valley Transit", "network:wikidata": "Q28451485", "operator": "Valley Transit"},
    "tld-1031": {"network": "Kochi Metro", "network:wikidata": "Q3522910"},
    "tld-1071": {
        # Zagrebački Električni Tramvaj
        "network": "ZET",
        "network:wikidata": "Q136060",
    },
    "tld-1200": {
        "network": "RTS Seneca",
        "network:wikidata": "Q128019467",
        "operator": "Rochester-Genesee Regional Transportation Authority",
        "operator:wikidata": "Q7353936",
    },
    "tld-1256": {
        # City of Santa Clarita Transit
        "network": "Santa Clarita Transit",
        "network:wikidata": "Q5123908",
    },
    "tld-1301": {"network": "Santa Ynez Valley Transit", "network:wikidata": "Q101538719"},
    "tld-1660_1": {"network": "Topeka Metro", "network:wikidata": "Q7824819"},
    "tld-1716_1": {
        # Toledo Area Regional Transit Authority
        "network": "TARTA",
        "network:wikidata": "Q7814150",
    },
    "tld-1717": {"network": "WRTA", "network:wikidata": "Q7988244", "operator": "Western Reserve Transit Authority"},
    "tld-3390": {
        # Jefferson Parish Transit
        "network": "JeT",
        "network:wikidata": "Q6175697",
    },
    "tld-4129": {
        # Gary Public Transportation Corporation
        "network": "GPTC",
        "network:wikidata": "Q5525788",
        "operator": "Gary Transit, Inc. & Gary Intercity Lines, Inc.",
    },
    "tld-4210": {"network": "Columbia County Rider", "network:wikidata": "Q107667623", "operator": "Columbia County"},
    "tld-4211": {
        "network": "Sunset Empire Transportation District",
        "network:wikidata": "Q7641258",
        "operator": "Clatsop County",
    },
    "tld-4298": {"network": "CAT", "network:wikidata": "Q5035468", "operator": "Capital Area Transit"},
    "tld-4385": {
        # Housatonic Area Regional Transit
        "network": "HARTransit",
        "network:wikidata": "Q5913491",
    },
    "tld-4470": {"network": "ORT", "network:wikidata": "Q7116506", "operator": "Ozark Regional Transit"},
    "tld-4506": {
        # Martin County Public Transit
        "network": "Marty",
        "network:wikidata": "Q128408071",
    },
    "tld-4668": {
        # Cooperative Alliance For Seacoast Transportation
        "network": "Cooperative Alliance for Seacoast Transportation",
        "network:wikidata": "Q5167873",
    },
    "tld-4669": {"network": "Altoona Metro Transit", "network:wikidata": "Q4736949"},
    "tld-4738": {"network": "Sarnia Transit", "network:wikidata": "Q7424351"},
    "tld-4777": {
        # Athens Clarke County Transit
        "network": "Athens Transit",
        "network:wikidata": "Q4813536",
    },
    "tld-4819": {"network": "Airdrie Transit", "network:wikidata": "Q4698613"},
    "tld-5509_1": {"network": "Prince Albert Transit", "network:wikidata": "Q7243789"},
    "tld-5536": {"network": "Transportes Coletivos do Barreiro", "network:wikidata": "Q81159859"},
    "tld-5547": {
        "network": "Imperial Valley Transit",
        "network:wikidata": "Q16980549",
        "operator": "First Transit",
        "operator:wikidata": "Q5453919",
    },
    "tld-5701": {
        # Koleje Małopolskie sp. z o.o.
        "network": "Autobusowych Linii Dowozowych",
        "operator": "Koleje Małopolskie",
        "operator:wikidata": "Q18609984",
    },
    "tld-5769": {
        # Kanawha Valley Regional Transportation Authority
        "network": "KRT",
        "network:wikidata": "Q6360825",
    },
    "tld-5788": {
        # MTA Metro-North Railroad
        "network": "Metro-North Railroad",
        "network:wikidata": "Q125908",
        "operator": "Metro-North Railroad",
        "operator:wikidata": "Q125908",
    },
    "tld-5873": {"network": "MAX", "network:wikidata": "Q6722682", "operator": "Macatawa Area Express"},
    "tld-5893": {
        # Billings Metropolitan Transit
        "network": "MET",
        "network:wikidata": "Q4911950",
    },
    "tld-5895": {"network": "Skagit Transit", "network:wikidata": "Q12054349"},
    "tld-6055": {
        "network": "Autobusowych Linii Dowozowych",
        "operator": "Koleje Małopolskie",
        "operator:wikidata": "Q18609984",
    },
    "tld-6684": {
        # Bermuda Department of Public Transportation
        "network": "Bermuda Public Transportation",
        "network:wikidata": "Q4892648",
    },
    "tld-6691": {
        # Réseau express métropolitain
        "network": "REM",
        "network:wikidata": "Q19582331",
    },
    "tld-6748": {
        "network": "NFTA Metro",
        "network:wikidata": "Q15114900",
        "operator": "Niagara Frontier Transportation Authority",
    },
    "tld-6758": {
        # Keretapi Tanah Melayu Berhad
        "operator": "Keretapi Tanah Melayu",
        "operator:wikidata": "Q1187590",
    },
    "tld-7040": {
        # Rochester-Genesee Regional Transportation Authority Genesee
        "network": "RTS Genesee",
        "network:wikidata": "Q128019449",
        "operator": "Rochester-Genesee Regional Transportation Authority",
        "operator:wikidata": "Q7353936",
    },
    "tld-7041": {
        # Rochester-Genesee Regional Transportation Authority Ontario
        "network": "RTS Ontario",
        "network:wikidata": "Q128019458",
        "operator": "Rochester-Genesee Regional Transportation Authority",
        "operator:wikidata": "Q7353936",
    },
    "tld-7042": {
        # Rochester-Genesee Regional Transportation Authority Orleans
        "network": "RTS Orleans",
        "network:wikidata": "Q128019463",
        "operator": "Rochester-Genesee Regional Transportation Authority",
        "operator:wikidata": "Q7353936",
    },
    "tld-7824": {
        # Bangor Community Connector
        "network": "Community Connector",
        "network:wikidata": "Q4834692",
    },
}


class GtfsSpider(CSVFeedSpider):
    name = "gtfs"
    start_urls = ["https://files.mobilitydatabase.org/feeds_v2.csv"]
    no_refs = True

    def parse_row(self, response, row):
        if row["status"] not in ("active", ""):
            return
        if row["data_type"] != "gtfs":
            return
        feed_attributes = {
            "country": row["location.country_code"],
            "state": row["location.subdivision_name"],
            "city": row["location.municipality"],
            "operator": row["provider"],
            "extras": {},
        }

        brand_tags = BRAND_MAPPING.get(row["id"], {})
        if "operator" in brand_tags:
            feed_attributes["operator"] = brand_tags["operator"]
        if "operator:wikidata" in brand_tags:
            feed_attributes["operator_wikidata"] = brand_tags["operator:wikidata"]
        if "network" in brand_tags:
            feed_attributes["extras"]["network"] = brand_tags["network"]
        if "network:wikidata" in brand_tags:
            feed_attributes["extras"]["network:wikidata"] = brand_tags["network:wikidata"]

        url = row["urls.latest"] or row["urls.direct_download"]
        self.logger.info("Provider: %s URL: %s", row["provider"], url)
        if url is not None:
            yield Request(url, self.parse_zip, cb_kwargs={"feed_attributes": feed_attributes})

    def parse_zip(self, response, feed_attributes):
        z = ZipFile(BytesIO(response.body))
        if "stops.txt" not in z.namelist():
            return

        agencies = {}
        if "agency.txt" in z.namelist():
            for row in csviter(z.read("agency.txt")):
                if agency_name := row.get("agency_name"):
                    if agency_id := row.get("agency_id"):
                        agencies[agency_id] = {"extras": {"network": agency_name}, "operator": agency_name}
                    else:
                        feed_attributes["extras"]["network"] = agency_name
                        feed_attributes["extras"]["operator"] = agency_name

        # Feed publisher is sometimes the transit agency, but more often the publishing service they use
        if 0 and "feed_info.txt" in z.namelist():
            for row in csviter(z.read("feed_info.txt")):
                if row.get("feed_publisher_name"):
                    feed_attributes["operator"] = row["feed_publisher_name"]

        if "attributions.txt" in z.namelist():
            for row in csviter(z.read("attributions.txt")):
                if row.get("is_operator") == "1" or row.get("is_authority") == "1":
                    feed_attributes["operator"] = row.get("organization_name")

        feed_attributes = {k: v for k, v in feed_attributes.items() if v}

        levels = {}
        if "levels.txt" in z.namelist():
            for row in csviter(z.read("levels.txt")):
                if "level_id" in row:
                    levels[row["level_id"]] = {"level": row.get("level_index"), "level:ref": row.get("level_name")}

        stop_routes = {}
        if "stop_times.txt" in z.namelist() and "trips.txt" in z.namelist() and "routes.txt" in z.namelist():
            routes = {route.get("route_id"): route for route in csviter(z.read("routes.txt"))}
            trips = {trip.get("trip_id"): trip for trip in csviter(z.read("trips.txt"))}
            for stop_time in csviter(z.read("stop_times.txt")):
                if not (trip := trips.get(stop_time.get("trip_id"))):
                    continue
                if not (stop_id := stop_time.get("stop_id")):
                    continue
                if not (route := routes.get(trip.get("route_id"))):
                    continue
                if stop_id in stop_routes:
                    stop_routes[stop_id].append(route)
                else:
                    stop_routes[stop_id] = [route]

        stopsdata = z.read("stops.txt")
        stop_id_names = {
            row["stop_id"]: row["stop_name"] for row in csviter(stopsdata) if "stop_id" in row and "stop_name" in row
        }
        # TODO: Localized (stop, agency) names from translations.txt
        for row in csviter(stopsdata):
            yield from self.parse_stop(response, row, levels, agencies, stop_id_names, stop_routes, feed_attributes)

    def parse_stop(self, response, row, levels, agencies, stop_id_names, stop_routes, feed_attributes):
        if not row.get("stop_lat") or not row.get("stop_lon"):
            return

        if row.get("location_type") == "3":
            # "Generic Node," only used for pathways
            return

        item = Feature(copy.deepcopy(feed_attributes))
        item["ref"] = row.get("stop_code")
        item["name"] = row.get("stop_name")
        item["lat"] = float(row.get("stop_lat"))
        item["lon"] = float(row.get("stop_lon"))
        item["website"] = row.get("stop_url")
        item["located_in"] = stop_id_names.get(row.get("parent_station"))
        item["extras"]["gtfs_id"] = row.get("stop_id")
        item["extras"]["name:pronunciation"] = row.get("tts_stop_name")
        item["extras"]["description"] = row.get("stop_desc")
        item["extras"]["loc_ref"] = row.get("platform_code")
        item["extras"].update(levels.get(row.get("level_id"), {}))

        routes = stop_routes.get(row.get("stop_id"), stop_routes.get(row.get("parent_station"), []))
        for route in routes:
            agency = agencies.get(route.get("agency_id"), {})
            for k, v in agency.items():
                if k == "extras":
                    for k2, v2 in v.items():
                        item["extras"][k2] = ";".join(filter(None, set((item["extras"].get(k2, "").split(";")) + [v2])))
                else:
                    item[k] = ";".join(filter(None, set((item.get(k, "").split(";")) + [v])))

        route_types = {route.get("route_type") for route in routes}
        apply_yes_no(
            Extras.WHEELCHAIR, item, row.get("wheelchair_boarding") == "1", row.get("wheelchair_boarding") != "2"
        )
        apply_yes_no("light_rail", item, "0" in route_types)
        apply_yes_no("subway", item, "1" in route_types)
        apply_yes_no("train", item, "2" in route_types)
        apply_yes_no("bus", item, "3" in route_types)
        apply_yes_no("ferry", item, "4" in route_types)
        apply_yes_no("tram", item, "5" in route_types)
        apply_yes_no("aerialway", item, "6" in route_types)
        apply_yes_no("trolleybus", item, "11" in route_types)
        apply_yes_no("monorail", item, "12" in route_types)

        if row.get("location_type") == "1":
            apply_category({"public_transport": "station"}, item)
            if not route_types.isdisjoint({"0", "1", "2", "5", "7", "12"}):
                apply_category({"railway": "station"}, item)
            if not route_types.isdisjoint({"3", "11"}):
                apply_category({"amenity": "bus_station"}, item)
        elif row.get("location_type") == "2":
            apply_category({"entrance": "yes"}, item)
            if "1" in route_types:
                apply_category({"railway": "subway_entrance"}, item)
            if not route_types.isdisjoint({"0", "2", "5", "7", "12"}):
                apply_category({"railway": "train_station_entrance"}, item)
        else:
            apply_category({"public_transport": "platform"}, item)
            if not route_types.isdisjoint({"0", "1", "2", "7", "12"}):
                apply_category({"railway": "halt"}, item)
            if not route_types.isdisjoint({"3", "11"}):
                apply_category({"highway": "bus_stop"}, item)
            if "5" in route_types:
                apply_category({"railway": "tram_stop"}, item)

        if row.get("location_type") != "2":
            if "0" in route_types:
                apply_category({"station": "light_rail"}, item)
            if "1" in route_types:
                apply_category({"station": "subway"}, item)
            if "2" in route_types:
                apply_category({"station": "train"}, item)
            if "4" in route_types:
                apply_category({"amenity": "ferry_terminal"}, item)
            if "5" in route_types:
                apply_category({"station": "tram"}, item)
            if "6" in route_types:
                apply_category({"aerialway": "station"}, item)
            if "7" in route_types:
                apply_category({"station": "funicular"}, item)
            if "12" in route_types:
                apply_category({"station": "monorail"}, item)

        item["extras"] = {k: v for k, v in item["extras"].items() if v}
        yield item
