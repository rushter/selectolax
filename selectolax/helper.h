#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <modest/finder/finder.h>
#include <myhtml/myhtml.h>
#include <myhtml/serialization.h>
#include <mycss/mycss.h>
#include <mycss/selectors/init.h>
#include <mycss/selectors/serialization.h>


myhtml_tree_node_t *get_html_node(myhtml_tree_t *html_tree);

void destroy_selector(modest_finder_t *finder,
                      myhtml_tree_t *html_tree,
                      mycss_entry_t *css_entry,
                      mycss_selectors_list_t *selectors_list,
                      myhtml_collection_t *collection);