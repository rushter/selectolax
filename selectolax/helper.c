/*
 Copyright (C) 2017 Artem Golubin
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <modest/finder/finder.h>
#include <myhtml/myhtml.h>
#include <myhtml/serialization.h>
#include <mycss/mycss.h>
#include <mycss/selectors/init.h>
#include <mycss/selectors/serialization.h>



myhtml_tree_node_t *get_html_node(myhtml_tree_t *html_tree) {
  return html_tree->node_html;
}


void destroy_selector(modest_finder_t *finder,
                      myhtml_tree_t *html_tree,
                      mycss_entry_t *css_entry,
                      mycss_selectors_list_t *selectors_list,
                      myhtml_collection_t *collection) {

  myhtml_collection_destroy(collection);
  mycss_selectors_list_destroy(mycss_entry_selectors(css_entry), selectors_list, true);
  modest_finder_destroy(finder, true);

  mycss_t *mycss = css_entry->mycss;
  mycss_entry_destroy(css_entry, true);
  mycss_destroy(mycss, true);

  myhtml_t *myhtml = html_tree->myhtml;
  myhtml_tree_destroy(html_tree);
  myhtml_destroy(myhtml);
}

