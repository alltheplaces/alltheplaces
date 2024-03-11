from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response


class DetectionRule:
    url: str = None
    headers: str = None

    def __init__(
        self,
        url: str = None,
        headers: str = None,
        *args,
        **kwargs,
    ):
        self.url = url
        self.headers = headers

    def __repr__(self):
        parameters = []
        if self.url:
            parameters.append('url="{}"'.format(self.url))
        if self.headers:
            parameters.append("headers='{}'".format(self.headers))
        return "DetectionRule({})".format(", ".join(parameters))


class DetectionRequestRule(DetectionRule):
    data: str = None

    def __init__(
        self,
        url: str = None,
        headers: str = None,
        data: str = None,
        *args,
        **kwargs,
    ):
        super().__init__(url, headers, *args, **kwargs)
        self.data = data

    def __repr__(self):
        parameters = []
        if self.url:
            parameters.append('url="{}"'.format(self.url))
        if self.headers:
            parameters.append("headers='{}'".format(self.headers))
        if self.data:
            parameters.append("data='{}'".format(self.data))
        return "DetectionRequestRule({})".format(", ".join(parameters))

    def __bool__(self):
        if self.url or self.headers or self.data:
            return True
        else:
            return False


class DetectionResponseRule(DetectionRule):
    js_objects: dict = {}
    xpaths: dict = {}

    def __init__(
        self,
        url: str = None,
        headers: str = None,
        js_objects: dict = {},
        xpaths: dict = {},
        *args,
        **kwargs,
    ):
        super().__init__(url, headers, *args, **kwargs)
        self.js_objects = js_objects
        self.xpaths = xpaths

    def __repr__(self):
        parameters = []
        if self.url:
            parameters.append('url="{}"'.format(self.url))
        if self.headers:
            parameters.append("headers='{}'".format(self.headers))
        if self.js_objects:
            parameters.append("js_objects={}".format(self.js_objects.__repr__()))
        if self.xpaths:
            parameters.append("xpaths={}".format(self.xpaths.__repr__()))
        return "DetectionResponseRule({})".format(", ".join(parameters))

    def __bool__(self):
        if self.url or self.headers or self.js_objects or self.xpaths:
            return True
        else:
            return False


class AutomaticSpiderGenerator:
    detection_rules: list[DetectionRule] = []

    @staticmethod
    def generate_spider_code(spider: Spider) -> str:
        """
        Generate source code representation of a spider class, where
        the generated source code is intended to be executable
        without further changes being required.
        :param spider: Spider class which should have a source code
                       representation generated for.
        :return: Generated source code (multi-line) of spider.
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
        :param spider: Spider class for which a source code
                       representation of attributes should be
                       generated.
        :param sort_order: Array of attribute key names which should
                           be printed into the textual representation
                           in the order specified. Other attributes
                           will be printed after this list in
                           alphabetical order.
        :return: Generated source code representation (multi-line)
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
                spider_attributes_code = "{}\n    {} = {{".format(spider_attributes_code, k)
                for k2, v2 in v.items():
                    if isinstance(v2, str):
                        spider_attributes_code = '{}\n        "{}": "{}",'.format(spider_attributes_code, k2, v2)
                    elif isinstance(v, int) or isinstance(v, float):
                        spider_attributes_code = '{}\n        "{}": {},'.format(spider_attributes_code, k2, v2)
                spider_attributes_code = "{}\n    }}".format(spider_attributes_code)
            elif isinstance(v, str):
                spider_attributes_code = '{}\n    {} = "{}"'.format(spider_attributes_code, k, v)
            elif isinstance(v, int) or isinstance(v, float):
                spider_attributes_code = "{}\n    {} = {}".format(spider_attributes_code, k, v)
            elif hasattr(v, "__len__"):  # Array
                spider_attributes_code = "{}\n    {} = [".format(spider_attributes_code, k)
                for v2 in v:
                    if isinstance(v2, str):
                        spider_attributes_code = '{}\n        "{}",'.format(spider_attributes_code, v2)
                    elif isinstance(v, int) or isinstance(v, float):
                        spider_attributes_code = "{}\n        {},".format(spider_attributes_code, v2)
                spider_attributes_code = "{}\n    ]".format(spider_attributes_code)
        return spider_attributes_code

    @staticmethod
    def request_storefinder_page(url: str) -> Iterable[Request]:
        """
        Method which store finder classes may choose to overwrite if
        the initial request to the store finder page should be more
        complex than simply loading the page in a Playwright browser.
        :param url: URL (as a string) of the store finder page which
                    should be the starting point for detecting the
                    presence of a store finder.
        :return: Scrapy Request object(s) or None.
        """
        yield None

    @staticmethod
    def storefinder_exists(response: Response) -> bool | Request:
        """
        Method which store finder classes should overwrite to return
        True if the response object is detected to have a particular
        store finder present. A store finder class may alternatively
        return a Scrapy Request object if additional requests need
        to be made to ascertain whether a store finder is in use.
        :param response: Scrapy response object for a given URL
                         which is being checked for the presence of
                         a store finder.
        :return: True if the store finder is detected, False
                 if a store finder is not detected, or a Scrapy
                 Request object if additional requests need to be
                 made to ascertain whether a store finder is in use.
                 Any Scrapy Request object returned must set
                 meta["next_detection_method"] callback method that
                 matches the return types for this
                 storefinder_exists method. A chain of requests
                 may occur, evenutally resulting in a boolean
                 return value.
        """
        return False

    @staticmethod
    def extract_spider_attributes(response: Response) -> dict | Request:
        """
        Method which store finder classes should overwrite to return
        a dictionary of attributes that can be extracted from the
        supplied response object. A store finder class may
        alternatively return a Scrapy Request object if additional
        requests need to be made to extract attributes. This may
        occur for example if the response contains an iframe, or some
        or all attributes need to be extracted from externally linked
        pages or JSON objects.
        :param response: Scrapy response object for a given URL
                         which is being checked for the presence of
                         a store finder.
        :return: A dictionary of attributes extracted from the
                 response, or a Scrapy Request object if additional
                 requests need to be made to extract a full set of
                 attributes.
                 Any Scrapy Request object returned must
                 set meta["next_extraction_method"] to a method
                 which returns the same types as this
                 extract_spider_attributes method.
                 The callback method for the Scrapy Request object
                 will be ignored.
                 If some attributes are extracted from the response
                 object, and further attributes are to be extracted
                 from a returned Scrapy Request object, the Scrapy
                 Request object must populate
                 meta["extracted_attributes"] with the partial set
                 of extracted attributes. The method specified by
                 meta["next_extraction_method"] can then append to
                 the set of extracted attributes and return either
                 the full set of attributes, or another Scrapy
                 Request object (causing this chain of requests to
                 continue until a dictionary of attributes is
                 returned in full).
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
