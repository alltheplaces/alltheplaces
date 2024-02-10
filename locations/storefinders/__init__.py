# Reference: https://docs.python.org/3/tutorial/modules.html#importing-from-a-package

from .agile_store_locator import AgileStoreLocatorSpider
from .amasty_store_locator import AmastyStoreLocatorSpider
from .amrest_eu import AmrestEUSpider
from .closeby import ClosebySpider
from .freshop import FreshopSpider
from .geo_me import GeoMeSpider
from .kibo import KiboSpider
from .limesharp_store_locator import LimesharpStoreLocatorSpider
from .localisr import LocalisrSpider
from .metalocator import MetaLocatorSpider
from .metizsoft import MetizsoftSpider
from .momentfeed import MomentFeedSpider
from .rexel import RexelSpider
from .shopapps import ShopAppsSpider
from .stockinstore import StockInStoreSpider
from .stockist import StockistSpider
from .store_locator_plus_cloud import StoreLocatorPlusCloudSpider
from .store_locator_plus_self import StoreLocatorPlusSelfSpider
from .storelocatorwidgets import StoreLocatorWidgetsSpider
from .storemapper import StoremapperSpider
from .storepoint import StorepointSpider
from .storerocket import StoreRocketSpider
from .super_store_finder import SuperStoreFinderSpider
from .sweetiq import SweetIQSpider
from .uberall import UberallSpider
from .virtualearth import VirtualEarthSpider
from .where2getit import Where2GetItSpider
from .woosmap import WoosmapSpider
from .wp_store_locator import WPStoreLocatorSpider
from .yext import YextSpider

__all__ = [
    "agile_store_locator",
    "amasty_store_locator",
    "amrest_eu",
    "closeby",
    "freshop",
    "geo_me",
    "kibo",
    "limesharp_store_locator",
    "localisr",
    "metalocator",
    "metizsoft",
    "momentfeed",
    "rexel",
    "shopapps",
    "stockinstore",
    "stockist",
    "store_locator_plus_cloud",
    "store_locator_plus_self",
    "storelocatorwidgets",
    "storemapper",
    "storepoint",
    "storerocket",
    "super_store_finder",
    "sweetiq",
    "uberall",
    "virtualearth",
    "where2getit",
    "woosmap",
    "wp_store_locator",
    "yext",
]
