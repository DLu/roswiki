import urllib2
from MoinMoin.Page import Page

from macroutils import wiki_url, get_repo_li, get_vcs_li, load_stack_release, \
     msg_doc_link, load_package_manifest, package_html_link, UtilException, load_stack_manifest, sub_link

def get_nav(macro, stack_name, packages):
    nav = '<script type="text/javascript" src="/js/roswiki.js"></script>'
    strong, text = macro.formatter.strong, macro.formatter.text

    if not stack_name or stack_name == 'sandbox':
        # ignore sandbox and non-stacked packages
        return nav
    elif [stack_name] == packages:
        # unary stack header
        return nav
        #return nav+strong(1)+text(stack_name)+strong(0)
    
    page_name = macro.formatter.page.page_name

    # create navigation elements for stack name
    if stack_name == page_name:
        top = strong(1)+text(stack_name)+strong(0)
    else:
        top = strong(1)+wiki_url(macro, stack_name)+strong(0)+text(': ')

    # create navigation elements for packages
    packages = [s for s in packages if not s.startswith('test_')]
    packages.sort()
    parts = []
    for pkg in packages:
        if pkg == page_name:
            parts.append(text(pkg))
        else:
            parts.append(wiki_url(macro, pkg))

    # assemble nav elements
    nav = em(1) + top 
    if parts:
        nav += text(': ')+parts[0]
        for part in parts[1:]:
            nav += text(' | ')+part
    nav += em(0)
    return nav
      
def is_stack_released(stack_name):
    stack_props = None
    for release_name in ['diamondback', 'cturtle', 'unstable', 'boxturtle']:
        if not stack_props:
            _, stack_props = load_stack_release(release_name, stack_name)
    return bool(stack_props)
    
def get_description(macro, data, type_):
    # keys
    authors = data.get('authors', 'unknown')
    try:
      if type(authors) != unicode:
        authors = unicode(authors, 'utf-8')
    except UnicodeDecodeError:
      authors = ''
    license = data.get('license', 'unknown')

    description = data.get('description', '')
    try:
        if type(description) != unicode:
            description = unicode(description, 'utf-8')
    except UnicodeDecodeError:
        description = ''

    f = macro.formatter
    p, div, li, ul = f.paragraph, f.div, f.listitem, f.bullet_list
    h, text, rawHTML = f.heading, f.text, f.rawHTML

    if type_ == 'stack':
        title = 'Stack Summary'
    else:
        title = 'Package Summary'
    try:
        repo_li = get_repo_li(macro, data)
        vcs_li = get_vcs_li(macro, data)

        # id=first for package?
        desc = h(1, 2, id="summary")+text(title)+h(0, 2)+\
               p(1,id="package-info")+rawHTML(description)+p(0)+\
               p(1,id="package-info")+ul(1)+\
               li(1)+text("Author: "+authors)+li(0)+\
               li(1)+text("License: "+license)+li(0)+\
               repo_li+\
               vcs_li+\
               ul(0)+p(0)
    except UnicodeDecodeError:
        desc = h(1, 2)+text(title)+h(0,2)+p(1)+text('Error retrieving '+title)+p(0)
    return desc
    
def get_package_links(macro, package_name, data):
    f = macro.formatter
    p, url, div = f.paragraph, f.url, f.div
    em, strong, h, text = f.emphasis, f.strong, f.heading, f.text
    li, ul = f.listitem, f.bullet_list

    review_status = data.get('review_status', 'unreviewed')
    external_documentation = data.get('external_documentation', '') or data.get('url', '') or '' 
    if 'ros.org' in external_documentation or 'pr.willowgarage.com' in external_documentation:
        external_documentation = u''

    msgs = data.get('msgs', [])
    srvs = data.get('srvs', [])

    #   -- link to msg/srv autogenerated docs
    msg_doc_title = "Msg/Srv API"
    if msgs and not srvs:
        msg_doc_title = "Msg API"
    elif srvs and not msgs:
        msg_doc_title = "Srv API"
    if msgs or srvs:
        msg_doc = li(1)+strong(1)+msg_doc_link(package_name, msg_doc_title)+strong(0)+li(0)
    else:
        msg_doc = text('')
    
    package_url = package_html_link(package_name)
    review_str = sub_link(macro, package_name, 'Reviews') + + text(' ('+review_status+')')
    dependency_tree = data.get('dependency_tree', '')
    if external_documentation:
        external_documentation = li(1)+strong(1)+url(1, url=external_documentation)+text("External Documentation")+url(0)+strong(0)+li(0)

    try:
        package_links = div(1, css_class="package-links")+\
                        strong(1)+text("Package Links")+strong(0)+\
                        ul(1)+\
                        li(1)+strong(1)+url(1, url=package_url)+text("Code API")+url(0)+strong(0)+li(0)+msg_doc+\
                        external_documentation+\
                        li(1)+sub_link(macro, package_name, 'Tutorials')+li(0)+\
                        li(1)+sub_link(macro, package_name, 'Troubleshooting')+li(0)+\
                        li(1)+review_str+li(0)+\
                        li(1)+url(1, url=dependency_tree)+text('Dependency Tree')+url(0)+li(0)+\
                        ul(0)
    except UnicodeDecodeError:
        package_links = div(1, css_class="package-links")
  
    package_links += get_dependency_list(macro, data, '')
    package_links+=div(0)
    return package_links

def get_stack_links(macro, stack_name, data, packages, is_unary):
    f = macro.formatter
    p, div, h, text = f.paragraph, f.div, f.heading, f.text
    li, ul, strong = f.listitem, f.bullet_list, f.strong

    is_released = is_stack_released(stack_name)
  
    # - links
    if is_released:
        releases_link = li(1)+Page(macro.request, '%s/Releases'%stack_name).link_to(macro.request, text='Releases')+li(0) 
    else:
        releases_link = ''
    if is_unary:
        troubleshooting_link = li(1)+sub_link(macro, stack_name, 'Troubleshooting')+li(0)
        review_status = data.get('review_status', 'unreviewed')
        review_link = li(1)+sub_link(macro, stack_name, 'Reviews') + text(' ('+review_status+')')+li(0)
        tutorials_link=li(1)+sub_link(macro, stack_name, 'Tutorials')+li(0)
    else:
        troubleshooting_link = review_link = tutorials_link = ''

    try:
        links = div(1, css_class="package-links")+strong(1)+text('Stack Links')+strong(0)+\
                ul(1)+\
                tutorials_link+\
                troubleshooting_link+\
                releases_link+\
                li(1)+sub_link(macro, stack_name, 'ChangeList', title='Change List')+li(0)+\
                li(1)+sub_link(macro, stack_name, 'Roadmap')+li(0)+\
                review_link+\
                ul(0)
    except UnicodeDecodeError:
        links = div(1, css_class="package-links")
  
    links += get_dependency_list(macro, data, 'stack-') + div(0)
    return links
    
def get_dependency_list(macro, data, css_prefix=''):
    f = macro.formatter
    li, ul, strong, div = f.listitem, f.bullet_list, f.strong, f.div
    
    depends = data.get('depends', [])
    depends_on = data.get('depends_on', [])
    
    links = ''
    if depends:
        depends.sort()
        links += strong(1)+\
                 '<a href="#" onClick="toggleExpandable(\'%sdependencies-list\');">Dependencies</a> (%s)'%(css_prefix, len(depends))+\
                 strong(0)+'<br />'+\
                 '<div id="%sdependencies-list" style="display:none">'%(css_prefix)+\
                 ul(1)
        for d in depends:
            links += li(1)+wiki_url(macro,d,shorten=20)+li(0)
        links += ul(0)+div(0)
    if depends_on:
        depends_on.sort()
        links += strong(1)+\
                 '<a href="#" onClick="toggleExpandable(\'%sused-by-list\');">Used by</a> (%s)'%(css_prefix, len(depends_on))+\
                 strong(0)+"<br />"+\
                 '<div id="%sused-by-list" style="display:none">'%(css_prefix)+ul(1) 
        for d in depends_on:
            links += li(1)+wiki_url(macro,d,shorten=20)+li(0)
        links += ul(0)+div(0)
        
    return links

