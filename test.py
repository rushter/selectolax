from selectolax.lexbor import LexborHTMLParser

html = """
        <head>
          <meta charset="utf-8">
          <meta content="width=device-width,initial-scale=1" name="viewport">
          <title>Title!</title>
          <!-- My crazy comment -->
          <p>Hello <strong>World</strong>!</p>
        </head>


        """
# html = "\n\n    <h1>Hello</h1>"
tree = LexborHTMLParser(html, is_fragment=True)
print(tree.root.html)
