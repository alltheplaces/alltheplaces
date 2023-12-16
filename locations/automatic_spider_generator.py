
from scrapy import Spider
from scrapy.http import Response


class AutomaticSpiderGenerator:
    @staticmethod
    def generate_spider_code(spider: Spider) -> str:
        """
        Generate source code representation of a spider class, where
        the generated source code is intended to be executable
        without further changes being required.
        :param spider: spider class which should have a source code
                       representation generated for.
        :return: generated source code (multi-line) of spider.
        """
        imports_list = ""
        superclasses = []
        for spider_base in spider.__bases__:
            imports_list = "{}from {} import {}\n".format(imports_list, spider_base.__module__, spider_base.__name__)
            superclasses.append(spider_base.__name__)
        superclasses_list = ", ".join(superclasses)

        spider_code = "{}\n\nclass {}({}):{}".format(
            imports_list,
            spider.__name__,
            superclasses_list,
            AutomaticSpiderGenerator.generate_spider_attributes_code(spider),
        )
        return spider_code

    @staticmethod
    def generate_spider_attributes_code(
        spider: Spider, sort_order: [] = ["name", "item_attributes", "allowed_domains", "start_urls"]
    ) -> str:
        """
        Generate source code representation of class attributes
        for a spider.
        :param spider: spider class for which a source code
                       representation of attributes should be
                       generated.
        :param sort_order: array of attribute key names which should
                           be printed into the textual representation
                           in the order specified. Other attributes
                           will be printed after this list in
                           alphabetical order.
        :return: generated source code representation (multi-line)
                 of class attributes.
        """
        spider_attributes_code = ""
        spider_attributes = {k: v for k, v in vars(spider).items() if not k.startswith("_") and v is not None}
        spider_attributes_sorted = {k: spider_attributes[k] for k in sort_order if k in spider_attributes}
        spider_attributes_sorted.update(
            {k: spider_attributes[k] for k in dict(sorted(spider_attributes.items())) if k not in sort_order}
        )
        for k, v in spider_attributes_sorted.items():
            if isinstance(v, dict):
                spider_attributes_code = "{}\n\t{} = {{".format(spider_attributes_code, k)
                for k2, v2 in v.items():
                    if isinstance(v2, str):
                        spider_attributes_code = '{}\n\t\t{} = "{}",'.format(spider_attributes_code, k2, v2)
                spider_attributes_code = "{}\n\t}}".format(spider_attributes_code)
            elif isinstance(v, str):
                spider_attributes_code = '{}\n\t{} = "{}"'.format(spider_attributes_code, k, v)
            elif hasattr(v, "__len__"):  # Array
                spider_attributes_code = "{}\n\t{} = [".format(spider_attributes_code, k)
                for v2 in v:
                    if isinstance(v2, str):
                        spider_attributes_code = '{}\n\t\t"{}",'.format(spider_attributes_code, v2)
                spider_attributes_code = "{}\n\t]".format(spider_attributes_code)
        return spider_attributes_code

    @staticmethod
    def storefinder_exists(response: Response) -> bool:
        """
        Method which store finder classes should overwrite to return
        True if the response object is detected to have a particular
        store finder present.
        :param response: Scrapy response object for a given URL
                         which is being checked for the presence of
                         a store finder.
        :return: True if the store finder is detected, False
                 otherwise.
        """
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict:
        """
        Method which store finder classes should overwrite to return
        a dictionary of attributes that can be extracted from the
        supplied response object.
        :param response: Scrapy response object for a given URL
                         which is being checked for the presence of
                         a store finder.
        :return: dictionary of attributes which have been able to be
                 extracted from the provided response object. An
                 example is {"api_key": "12345"}.
        """
        return {}

    def __init_subclass__(cls, **kwargs):
        if "brand_wikidata" in kwargs.keys() and kwargs["brand_wikidata"]:
            if not hasattr(cls, "item_attributes"):
                cls.item_attributes = {}
            cls.item_attributes["brand_wikidata"] = kwargs["brand_wikidata"]
            if "brand" in kwargs.keys() and kwargs["brand"]:
                cls.item_attributes["brand"] = kwargs["brand"]

        if "operator_wikidata" in kwargs.keys() and kwargs["operator_wikidata"]:
            if not hasattr(cls, "item_attributes"):
                cls.item_attributes = {}
            cls.item_attributes["operator_wikidata"] = kwargs["operator_wikidata"]
            if "operator" in kwargs.keys() and kwargs["operator"]:
                cls.item_attributes["operator"] = kwargs["operator"]

        if "spider_key" in kwargs.keys() and kwargs["spider_key"]:
            cls.name = kwargs["spider_key"]

        if "extracted_attributes" in kwargs.keys() and kwargs["extracted_attributes"]:
            for k, v in kwargs["extracted_attributes"].items():
                setattr(cls, k, v)
