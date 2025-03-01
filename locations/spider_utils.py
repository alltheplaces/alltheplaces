from typing import Any, Generator, Type

from scrapy.utils.misc import walk_modules
from scrapy.utils.spider import iter_spider_classes

from locations.settings import SPIDER_MODULES


def find_spider_class_from_name(spider_name: str) -> type | None:
    if not spider_name:
        return None
    for spider_class in iter_spider_classes_in_all_modules():
        if spider_name == spider_class.name:
            return spider_class
    return None


def iter_spider_classes_in_all_modules() -> Generator[Type[Spider], Any, None]:
    for mod in SPIDER_MODULES:
        for module in walk_modules(mod):
            for spider_class in iter_spider_classes(module):
                yield spider_class
