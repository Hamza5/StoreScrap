import abc
import re
import scrapy


class StoreScrapSpider(abc.ABC, scrapy.Spider):

    brand_values = {
        'Admiral': None,
        'Hisense': None,
        'Konka': None,
        'Samsung': None,
    }

    def __init__(self, brands=tuple(brand_values.keys()), **kwargs):
        super().__init__(**kwargs)
        self.brands = brands
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "Origin": self.origin,
            "Connection": "keep-alive",
            "Referer": self.origin,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers"
        }
        self.cookies = {}

    UPPER_LETTERS_NUMBERS_RE = re.compile(r'[A-Z0-9/]+[A-Z][A-Z0-9/]+', re.ASCII | re.IGNORECASE)

    def get_model_code(self, product_name):
        candidates = sorted(self.UPPER_LETTERS_NUMBERS_RE.findall(product_name), key=len, reverse=True)
        return candidates[0] if candidates else ''

    @property
    @abc.abstractmethod
    def origin(self):
        pass
