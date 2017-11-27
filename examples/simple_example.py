from selectolax.parser import HtmlParser

html = "<div><p id=p1><p id=p2><p id=p3><a>link</a><p id=p4><p id=p5>text<p id=p6></div>"
selector = "div > :nth-child(2n+1):not(:has(a))"

for node in HtmlParser(html).css(selector).find():
    print(node.attributes, node.text, node.tag)
    print(node.parent.tag)
    print(node.html)
