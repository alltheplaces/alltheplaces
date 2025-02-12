from typing import Any, AsyncGenerator, Iterable, Iterator, override
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import CSVFeedSpider
from scrapy.utils.defer import maybe_deferred_to_future
from twisted.internet.defer import Deferred, DeferredList

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.items import Feature

# General Bikeshare Feed Specification
# https://gbfs.mobilitydata.org/

# GBFS is a standardized API for operators of bicycles, scooters, moped, and car rental service providers. This
# spider stats at https://github.com/MobilityData/gbfs which offers a centralised catalog of networks or "systems".
# It then processes each system and collects the docks or "stations" from it. Not every system has stations as some
# are dockless.

BRAND_MAPPING = {
    "BA": {"brand": "Bay Wheels", "brand_wikidata": "Q16971391"},
    "bcycle_bublr": {"brand": "Bublr Bikes", "brand_wikidata": "Q108789295"},
    "bcycle_indego": {"brand": "Indego", "brand_wikidata": "Q19876452"},
    "bcycle_memphis": {"brand": "Explore Bike Share", "brand_wikidata": "Q86706492"},
    "bergen-city-bike": {"brand": "Bergen Bysykkel", "brand_wikidata": "Q109288835"},
    "bicimad_madrid": {"brand": "BiciMAD", "brand_wikidata": "Q17402113"},
    "bici_madrid": {"brand": "BiciMAD", "brand_wikidata": "Q17402113"},
    "bike_barcelona": {"brand": "Bicing", "brand_wikidata": "Q1833385"},
    "bike_buenosaires": {"brand": "BA Ecobici", "brand_wikidata": "Q18419538"},
    "bike_share_toronto": {"brand": "Bike Share Toronto", "brand_wikidata": "Q17018523"},
    "biketobike": {"brand": "Mi Bici Tu Bici", "brand_wikidata": "Q100272303"},
    "BIKI_valladolid": {"brand": "Biki", "brand_wikidata": "Q111760142"},
    "bird-bordeaux": {"brand": "Bird"},
    "bird-cascais": {"brand": "Bird"},
    "bird-chalonsenchampagne": {"brand": "Bird"},
    "bird-draguignan": {"brand": "Bird"},
    "bird-larochesuryon": {"brand": "Bird"},
    "bird-laval": {"brand": "Bird"},
    "bird-millau": {"brand": "Bird"},
    "bird-montlucon": {"brand": "Bird"},
    "bird-sarreguemines": {"brand": "Bird"},
    "bird-vichy": {"brand": "Bird"},
    "Bixi_MTL": {"brand": "Bixi", "brand_wikidata": "Q4919302"},
    "bluebike": {"brand": "Blue-bike", "brand_wikidata": "Q17332642"},
    "bluebikes": {"brand": "Bluebikes", "brand_wikidata": "Q3142157"},
    "BoltEU_Brussels": {"brand": "Bolt", "brand_wikidata": "Q20529164"},
    "cabi": {"brand": "Capital Bikeshare", "brand_wikidata": "Q1034635"},
    "callabike": {"brand": "Call a Bike", "brand_wikidata": "Q1060525"},
    "callabike_ice": {"brand": "Call a Bike", "brand_wikidata": "Q1060525"},
    "cc_smartbike_antwerp": {"brand": "Velo", "brand_wikidata": "Q2413118"},
    "chicago": {"brand": "Divvy", "brand_wikidata": "Q16973938"},
    "cogo": {"brand": "CoGo Bike Share", "brand_wikidata": "Q91342219"},
    "docomo-cycle-tokyo": {"brand": "Docomo Bike Share", "brand_wikidata": "Q55533296"},
    "donkey_aalborg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_aarhus": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_am": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_antwerp": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_ballerup": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_bamberg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_budapest": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_cheltenham_spa": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_cirencester": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_copenhagen": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_den_haag": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_dordrecht": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_frederikshavn": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_ge": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_gh": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_glostrup": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_gorinchem": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_hillerod": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_iisalmi": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_imatra": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kiel": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kingham": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_klampenborg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kotka": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kouvola": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_kreuzlingen": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_lappeenranta": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_le_locle": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_li": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_maentsaelae": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_malmoe": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_mikkeli": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_moreton_in_marsh": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_munich": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_neuchatel": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_odense": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_oxford": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_porvoo": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_raasepori": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_regensburg": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_reykjavik": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_riihimaki": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_rotterdam_den_haag": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_rt": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_store_heddinge": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_the_cotswold_water_park": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_thun": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_turku": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_ut": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_valenciennes": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_worthing": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "donkey_yverdon-les-bains": {"brand": "Donkey Republic", "brand_wikidata": "Q63753939"},
    "dott-aachen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-aalst": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-abu-dhabi": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-alghero": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-arezzo": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-arzachena": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-baden-bei-wien": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-banska-bystrica": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bari": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-basel": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-basildon": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bath": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-baunatal": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-berlin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bialogard": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bielawa": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bielefeld": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-boblingen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bochum": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bonn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bordeaux": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bourgoin-jallieu": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-braintree": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-braniewo": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bratislava": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bregenz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bristol": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-brodnica": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bruhl": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-brunswick": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-brussels": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-budapest": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-bytom": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-cagliari": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-casgbs": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-catania": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-celle": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-charleroi": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-chelmsford": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-chemnitz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-chrzanow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-colchester": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-cologne": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-copenhagen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-cottbus": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-darmstadt": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-detmold": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-doha": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dornbirn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dortmund": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dubai": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dubai-hills": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-duisburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dusseldorf": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dzierzoniow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-dziwnow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-eindhoven": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-elblag": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-erfurt": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-erlangen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-essen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-estepona": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-feldkirchen-bei-graz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ferrara": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-flensburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-frankfurt": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-friedrichshafen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-fuerteventura": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gdansk": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gera": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ghent": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gifhorn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-godollo": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-goleniow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gpseo": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-greifswald": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-grenoble": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-grodzisk-mazowiecki": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-grudziadz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gryfino": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gutersloh": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-gyor": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-hamburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-hamm": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-hannover": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-heidelberg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-heilbronn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-helsingborg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-hennef": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-herford": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-herne": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-herten": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-hilden": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-hildesheim": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ibiza": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-iława": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ingolstadt": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-innsbruck": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-jastrzebie-zdroj": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-jaworzno": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-jeddah": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-jena": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kaiserslautern": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kalisz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-karlsruhe": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kassel": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-katowice": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kiel": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-klagenfurt": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kołobrzeg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-konin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-korneuburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-koscierzyna": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kosice": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-koszalin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-krakow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-kwidzyn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-langenfeld": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lanzarote": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lebork": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-leipzig": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-leoben": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-leszno": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lidkoping": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-liege": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lindau": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-linz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lubeck": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lubliniec": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ludwigsburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-łukow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-lyon": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-madrid": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-mainz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-malaga": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-malbork": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-mannheim": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-marseille": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-martin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-meerbusch": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-michalovce": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-miedzyzdroje": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-mielec": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-mikołow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-milan": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-milton-keynes": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-minden": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-miskolc": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-modena": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-modling": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-monchengladbach": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-monheim-am-rhein": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-monza": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-mulheim-an-der-ruhr": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-munich": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-munster": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-murcia": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-namur": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-neumunster": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-neuss": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-nowogard": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-nowy-dwor-mazowiecki": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-nowy-sacz": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-nuremberg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-nysa": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ol-vallee": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-olesnica": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-osnabruck": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ostroda": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-oswiecim": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-paderborn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-padua": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-palermo": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-paris": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-partille": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-peine": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-petah-tikva": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-pezinok": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-piekary-slaskie": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-police": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-poznan": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-prawobrzeze": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-presov": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-prievidza": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-pruszcz-gdanski": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-pruszkow": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ras-al-khaimah": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-recklinghausen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-regensburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-reggio-emilia": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-reutlinge": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-rewal": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-rheda-wiedenbruck": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-rheine": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-riccione": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-riyadh": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-romanshorn": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-rome": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-rostock": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ruda-slaska": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-russelsheim": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-saarbrucken": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-saint-quentin-en-yvelines": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-salzgitter": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-sankt-augustin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-schaffhausen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-seville": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-sharjah": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-siedlce": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-siemu": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-siofok": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-skawina": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-słupsk": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-sobieszewo-island": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-solingen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-st.-gallen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-starogard-gdanski": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-steyr": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-stockholm": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-stuttgart": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-swidnica": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-swinoujscie": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-szczecin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tarnowskie-gory": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tarragona": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tczew": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tel-aviv": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tenerife": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tenerife-sur": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tignes": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-trento": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tricity": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-trnava": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-troisdorf": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-trollhattan": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-trzebnica": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-tubingen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-turin": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-uberlingen": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ulm": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-utrecht": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-val-d’iser": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-varese": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-varnamo": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-verona": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-villach": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-warsaw": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-wels": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-wiesbaden": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-winterthur": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-wolfsburg": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-wrocław": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-zawiercie": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-ziar-nad-hronom": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-zory": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-zurich": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "dott-zwickau": {"brand": "Dott", "brand_wikidata": "Q107463014"},
    "go_biki": {"brand": "Biki", "brand_wikidata": "Q98337927"},
    "hellocycling": {"brand": "HELLO CYCLING", "brand_wikidata": "Q91231927"},
    "inurba-gdansk": {"brand": "Mevo", "brand_wikidata": "Q60860236"},
    "lyft_dca": {"brand": "Capital Bikeshare", "brand_wikidata": "Q1034635"},
    "lyft_den": {"brand": "Lyft", "brand_wikidata": "Q17077936"},
    "MEX": {"brand": "Ecobici", "brand_wikidata": "Q5817067"},
    "netbike_bg": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "neuron_dud": {"brand": "Neuron Mobility"},
    "nextbike_ba": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_bh": {"brand": "MOL Bubi", "brand_wikidata": "Q16971969"},
    "nextbike_bn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_bu": {"brand": "Belfast Bikes", "brand_wikidata": "Q19843240"},
    "nextbike_ch": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_co": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_cq": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_cu": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_cy": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_dd": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_dj": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_dk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_do": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ff": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_gg": {"brand": "OVO Bikes", "brand_wikidata": "Q120450856"},
    "nextbike_hr": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ib": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ka": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_kn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ko": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_la": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_le": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_li": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_lv": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_mz": {"brand": "MVGmeinRad", "brand_wikidata": "Q14541300"},
    "nextbike_na": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nc": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ng": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nh": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nm": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nr": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nt": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nu": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_nw": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_pj": {"brand": "SRM Jaskółka", "brand_wikidata": "Q119107871"},
    "nextbike_sl": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_td": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_te": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tf": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tg": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_th": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ti": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tj": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tl": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_to": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tq": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ts": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tt": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tu": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tv": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tx": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ty": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_tz": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_ud": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uf": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uk": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uo": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_uv": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_vr": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_wn": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_wr": {"brand": "WienMobil Rad", "brand_wikidata": "Q111794110"},
    "nextbike_xa": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_xb": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_xc": {"brand": "Nextbike", "brand_wikidata": "Q2351279"},
    "nextbike_zz": {"brand": "Metrorower", "brand_wikidata": "Q123507620"},
    "NYC": {"brand": "Citi Bike", "brand_wikidata": "Q2974438"},
    "openvelo_aachen_velocity": {"brand": "Velocity Aachen", "brand_wikidata": "Q102348696"},
    "oslobysykkel": {"brand": "Oslo Bysykkel", "brand_wikidata": "Q7107010"},
    "Paris": {"brand": "Vélib' Metropole", "brand_wikidata": "Q1120762"},
    "peacehealth_rides": {"brand": "PeaceHealth Rides", "brand_wikidata": "Q115393175"},
    "pony_Angers": {"brand": "Pony"},
    "pony_Basque_Country": {"brand": "Pony"},
    "pony_Beauvais": {"brand": "Pony"},
    "pony_Beziers": {"brand": "Pony"},
    "pony_bordeaux": {"brand": "Pony"},
    "pony_Bourges": {"brand": "Pony"},
    "pony_brussels": {"brand": "Pony"},
    "pony_Charleroi": {"brand": "Pony"},
    "pony_Evry": {"brand": "Pony"},
    "pony_Herouville": {"brand": "Pony"},
    "pony_La_Roche_Sur_Yon": {"brand": "Pony"},
    "pony_liège": {"brand": "Pony"},
    "pony_Limoges": {"brand": "Pony"},
    "pony_Lorient": {"brand": "Pony"},
    "pony_Nice": {"brand": "Pony"},
    "pony_Olivet": {"brand": "Pony"},
    "pony_paris": {"brand": "Pony"},
    "pony_Perpignan": {"brand": "Pony"},
    "pony_poitiers": {"brand": "Pony"},
    "publibike": {"brand": "PubliBike", "brand_wikidata": "Q3555363"},
    "regiorad_stuttgart": {"brand": "RegioRad Stuttgart", "brand_wikidata": "Q57274085"},
    "relay_bike_share": {"brand": "Relay Bike Share", "brand_wikidata": "Q48798195"},
    "sharedmobility.ch": {"brand": "Shared Mobility"},
    "stadtrad_hamburg": {"brand": "StadtRAD Hamburg", "brand_wikidata": "Q2326366"},
    "tier_basel": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_bern": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_paris": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_stgallen": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_winterthur": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "tier_zurich": {"brand": "TIER", "brand_wikidata": "Q63386916"},
    "velospot_ch": {"brand": "Velospot", "brand_wikidata": "Q56314221"},
    "voi_ch": {"brand": "Voi", "brand_wikidata": "Q61650427"},
    "voi_Marseille": {"brand": "Voi", "brand_wikidata": "Q61650427"},
}

FORM_FACTOR_MAP = {
    "bicycle": {"amenity": "bicycle_rental"},
    "cargo_bicycle": {"amenity": "bicycle_rental", "rental": "cargo_bike"},
    "car": {"amenity": "car_sharing"},
    "moped": {"amenity": "motorcycle_rental"},
    "scooter_standing": {"amenity": "kick-scooter_rental"},
    "scooter_seated": {"amenity": "kick-scooter_rental"},
}

PARKING_TYPE_MAP = {
    "parking_lot": "surface",
    "street_parking": "lane",
    "underground_parking": "underground",
    "sidewalk_parking": "on_kerb",
}


class GbfsSpider(CSVFeedSpider):
    name = "gbfs"
    start_urls = ["https://github.com/MobilityData/gbfs/raw/master/systems.csv"]
    download_delay = 2
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def get_authorized_url(self, url: str, authentication_info: str) -> str | None:
        """Adds authentication_info to the url if it's not already part of it,
        or returns None if authentication_info is a link to instructions."""
        if authentication_info == "":
            return url
        if authentication_info.startswith("http"):
            return None
        parsed = urlparse(url)
        qs = urlencode(parse_qsl(parsed.query) + parse_qsl(authentication_info))
        parsed._replace(query=qs)
        return urlunparse(parsed)

    @override
    def parse_row(self, response: Response, row: dict[str, str]) -> Iterator[Request]:
        """Queues downloads for every GBFS system manifest"""
        if url := self.get_authorized_url(row["Auto-Discovery URL"], row["Authentication Info"]):
            yield JsonRequest(url=url, cb_kwargs=row, callback=self.parse_gbfs)

    def set_localized_name(
        self, item: Feature | dict[str, Any], itemkey: str, station: dict[str, Any], stationkey: str
    ):
        """Utility function to set localized tags"""
        if stationkey not in station:
            return
        value = station[stationkey]
        if isinstance(value, str):
            if itemkey in ("name", "brand", "operator"):
                item[itemkey] = value
            else:
                item["extras"][itemkey] = value
        elif isinstance(value, list):
            for translation in value:
                item["extras"][f"{itemkey}:{translation['language']}"] = translation["text"]
        else:
            self.logger.error(f"Can't handle a localized {stationkey!r} of type {type(value)}")

    def defer_request_feed(
        self,
        all_feeds: Iterable[dict[str, Any]],
        feed_name: str,
        deferreds: list[Deferred[Response]],
        authentication_info: str,
    ) -> bool:
        """Given the name of a GBFS feed, look for it in the feeds list, and
        queue an asynchronous download"""
        # List feeds by name.
        feeds = [feed for feed in all_feeds if feed["name"] == feed_name]

        # If any feeds by that name exist, request the first.
        if len(feeds) > 0 and (url := self.get_authorized_url(feeds[0]["url"], authentication_info)):
            assert self.crawler.engine is not None
            deferreds.append(self.crawler.engine.download(JsonRequest(url=url)))
            return True
        else:
            return False

    def get_next_json(self, has_feed: bool, responses: list[tuple[bool, Response]]) -> Any | None:
        """Get a feed from the list of responses, if we requested that feed"""
        if has_feed:
            success, response = responses.pop(0)
            if success:
                try:
                    return response.json()
                except ValueError as e:
                    self.logger.exception(e)
        return None

    def get_shared_attributes_from_row(self, **kwargs) -> dict[str, Any]:
        """Shared attributes for every item in a system, given the system's row in the CSV"""
        # "network" is a better place than "brand" for the "system name," since a brand can have many non-interoperable networks
        shared_attributes: dict[str, Any] = {"country": kwargs["Country Code"], "extras": {"network": kwargs["Name"]}}

        # TODO: Map all brands/names
        if kwargs["System ID"] in BRAND_MAPPING:
            shared_attributes.update(BRAND_MAPPING[kwargs["System ID"]])
        else:
            # In the absence of a known brand mapping, use the network name.
            shared_attributes["brand"] = kwargs["Name"]

        return shared_attributes

    def update_attributes_from_system_information(
        self, system_information: dict[str, Any], shared_attributes: dict[str, Any]
    ):
        """Shared attributes for every item in a system, given the system's "system_information" feed"""
        system_information = system_information.get("data", system_information)

        self.set_localized_name(shared_attributes, "network", system_information, "name")

        if "opening_hours" in system_information:
            shared_attributes["opening_hours"] = system_information["opening_hours"]

        self.set_localized_name(shared_attributes, "network:short", system_information, "short_name")
        self.set_localized_name(shared_attributes, "operator", system_information, "operator")

    def get_vehicle_types_categories(self, vehicle_types: Any) -> dict[Any, dict[str, str]]:
        """Create a map from vehicle_type ID to OSM category using the system's "vehicle_types" feed"""
        vehicle_types_categories = {}
        for vehicle_type in DictParser.get_nested_key(vehicle_types, "vehicle_types") or []:
            cat = dict(FORM_FACTOR_MAP.get(vehicle_type["form_factor"], {}))
            if vehicle_type.get("propulsion_type") == "electric_assist":
                if "rental" in cat:
                    cat["rental"] += ";ebike"
                else:
                    cat["rental"] = "ebike"
            vehicle_types_categories[vehicle_type["vehicle_type_id"]] = cat
        return vehicle_types_categories

    def get_station_status_categories(
        self, station_status: Any, vehicle_types_categories: dict[Any, dict[str, str]]
    ) -> dict[Any, list[dict[str, str]]]:
        """If a station in station_information doesn't have vechicle_type tags, get it from the "station_status" feed."""
        station_status_categories = {}
        for station in DictParser.get_nested_key(station_status, "stations") or []:
            station_status_categories[station["station_id"]] = [
                vehicle_types_categories.get(vehicle_type["vehicle_type_id"], {})
                for vehicle_type in station.get("vehicle_types_available", [])
            ]
        return station_status_categories

    async def parse_gbfs(self, response: Response, **kwargs) -> AsyncGenerator[Feature, None]:
        """Process one GBFS system."""
        try:
            data = response.json()
        except ValueError as e:
            self.logger.exception(e)
            return

        feeds = DictParser.get_nested_key(data, "feeds") or []
        deferreds: list[Deferred[Response]] = []
        authentication_info = kwargs["Authentication Info"]

        # Network and operator information
        has_system_information = self.defer_request_feed(feeds, "system_information", deferreds, authentication_info)

        # Vehicle types, used to determine feature category
        has_vehicle_types = self.defer_request_feed(feeds, "vehicle_types", deferreds, authentication_info)

        # Information about each docking station
        has_station_information = self.defer_request_feed(feeds, "station_information", deferreds, authentication_info)

        # Current status of each docking station.
        # Only needed as fallback if station_information doesn't have vehicle type tags.
        has_station_status = self.defer_request_feed(feeds, "station_status", deferreds, authentication_info)

        if not has_station_information:
            # Can't proceed without station locations.
            self.logger.info(f"{kwargs['Name']}/{kwargs['System ID']} has no station locations")
            return

        # Send off all requests in parallel.
        responses = await maybe_deferred_to_future(DeferredList(deferreds))

        # Retrieve the responses in the same order.
        system_information = self.get_next_json(has_system_information, responses)
        vehicle_types = self.get_next_json(has_vehicle_types, responses)
        station_information = self.get_next_json(has_station_information, responses)
        station_status = self.get_next_json(has_station_status, responses)

        # Build a list of attributes common to all stations in this system.
        shared_attributes = self.get_shared_attributes_from_row(**kwargs)

        if isinstance(system_information, dict):
            self.update_attributes_from_system_information(system_information, shared_attributes)

        vehicle_types_categories = {} if vehicle_types is None else self.get_vehicle_types_categories(vehicle_types)
        station_status_categories = (
            {}
            if station_status is None
            else self.get_station_status_categories(station_status, vehicle_types_categories)
        )

        # Now scrape the stations.
        for station in DictParser.get_nested_key(station_information, "stations") or []:
            yield self.parse_station(
                station, shared_attributes, vehicle_types_categories, station_status_categories, **kwargs
            )

    def parse_station(
        self,
        station: Any,
        shared_attributes: dict[str, Any],
        vehicle_types_categories: dict[Any, dict[str, str]],
        station_status_categories: dict[Any, list[dict[str, str]]],
        **kwargs,
    ) -> Feature:
        """Process an individual GBFS station."""
        item = Feature(**shared_attributes)
        item["ref"] = item["extras"]["ref:gbfs"] = f"{kwargs['System ID']}:{station['station_id']}"
        item["extras"][f"ref:gbfs:{kwargs['System ID']}"] = str(station["station_id"])
        item["lat"] = station["lat"]
        item["lon"] = station["lon"]
        item["street_address"] = station.get("address")
        item["postcode"] = station.get("post_code")
        item["opening_hours"] = station.get("station_opening_hours")
        item["geometry"] = station.get("station_area")
        item["extras"]["parking"] = PARKING_TYPE_MAP.get(station.get("parking_type"))
        item["phone"] = station.get("contact_phone")
        item["website"] = station.get("rental_uris", {}).get("web")

        self.set_localized_name(item, "name", station, "name")
        self.set_localized_name(item, "short_name", station, "short_name")

        if "capacity" in station:
            item["extras"]["capacity"] = str(station["capacity"])

        if station.get("is_charging_station"):
            apply_category(Categories.CHARGING_STATION, item)

        if station.get("is_virtual_station", None) is False:
            # If true, "the station is a location *without* smart docking
            # infrastructure." (emphasis added)
            # So, if true or absent, it could be a drop-off location, or a
            # purely virtual station.
            # If false, it must be a docking station.
            item["extras"]["bicycle_rental"] = "docking_station"

        rental_methods = station.get("rental_methods", [])
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, "creditcard" in rental_methods)
        apply_yes_no(PaymentMethods.APPLE_PAY, item, "applepay" in rental_methods)
        apply_yes_no(PaymentMethods.GOOGLE_PAY, item, "androidpay" in rental_methods)

        # Try to determine the feature type based on its capacity of vehicle types
        vehicle_types_capacity = station.get("vehicle_types_capacity", [])
        vehicle_docks_capacity = station.get("vehicle_docks_capacity", [])
        total_vehicle_capacity = vehicle_types_capacity + vehicle_docks_capacity
        if len(total_vehicle_capacity) > 0:
            for vehicle_capacity in total_vehicle_capacity:
                for vehicle_type_id in vehicle_capacity["vehicle_type_ids"]:
                    cat = vehicle_types_categories.get(vehicle_type_id, {})
                    apply_category(cat, item)
                    # Additionally, specify the capacity of each vehicle type
                    if "rental" in cat and vehicle_capacity.get("count") is not None:
                        for biketype in cat["rental"].split(";"):
                            capacity_key = f"capacity:{biketype}"
                            capacity = item["extras"].get(capacity_key, 0)
                            capacity += vehicle_capacity["count"]
                            item["extras"][capacity_key] = capacity
        # If it doesn't specify the vehicle capacity, check if the "station_status" feed has the current vehicles stored
        elif station["station_id"] in station_status_categories:
            for cat in station_status_categories[station["station_id"]]:
                apply_category(cat, item)

        # If neither the vehicle type nor a brand preset were available, set a fallback category.
        if "amenity" not in item["extras"] and not item.get("brand_wikidata"):
            apply_category({"public_transport": "platform"}, item)

        return item
