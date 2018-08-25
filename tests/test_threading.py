# coding:utf-8
import multiprocessing
import threading

import pytest as pytest
from selectolax.parser import HTMLParser

CPU_COUNT = multiprocessing.cpu_count()


def worker():
    for i in range(500):
        html = "<span></span><div><p class='p3'>text</p><p class='p3'>sd</p></div><p></p>"
        selector = "p.p3"
        tree = HTMLParser(html)

        assert tree.css_first(selector).text() == 'text'

        for tag in tree.css('p'):
            tag.decompose()

        for tag in tree.css('span'):
            tag.decompose()


def test_multithreading():
    # A dumb way to test multithreading "safety"

    pool = []
    for _ in range(CPU_COUNT*2):
        th = threading.Thread(target=worker)
        th.start()
        pool.append(th)

    for th in pool:
        th.join()
