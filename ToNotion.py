import urllib
from urllib import request
import json
import requests
import sys
from xml.dom.minidom import parse
from xml.dom.minidom import parseString
import re
import os

def title_strip(title:str):
    rule = re.compile(r'[-,$()#+&* :]')
    title = re.split(rule, title)
    title = " ".join(title)
    title = title.lower()
    return title


def to_tag(string: str, default_tag='ArXiv'):
    tag = string.split('(')[-1].split('to')[-1].replace(' ','')
    rule = re.compile(r'[-,$()#+&* :]')
    tag = re.split(rule, tag)
    tag = ".".join(title)
    if len(tag) > 10:
        tag = default_tag
    return tag


def get_search_url(server: str, max_result: int, entry:str):
    if server == 'semantic':
        search_url = "https://api.semanticscholar.org/graph/v1/paper/search?query="
        search_url += urllib.request.quote(entry.encode('utf-8'))
        search_url += "&limit=" + str(max_result)
        search_url += "&offset=0"
        search_url += "&fields=externalIds,url,title"
    elif server == 'arxiv':
        search_url = "http://export.arxiv.org/api/query?search_query="
        search_url += urllib.request.quote(entry.encode('utf-8'))
        search_url += "&start=0"
        search_url += "&max_results=" + str(max_result)
    elif server == 'semantic_id':
        search_url = "https://api.semanticscholar.org/graph/v1/paper/"
        search_url += entry
        search_url += "?fields=authors,year,venue,abstract,tldr,references"
    return search_url


def semantic_details(paper: dict):
    ## 3 get abstract, year, tldr, authors, venue
    ### create the detailed search_url
    search_url = get_search_url('semantic_id', 1, paper['paperId'])
    ### get detailed paper data from search
    res = urllib.request.urlopen(search_url).read()
    res = json.loads(res)
    #### Stuck info into dictionary {paper}
    ##### - abstract
    paper['abstract'] = res['abstract']
    ##### - source
#     paper['source'] = []
#     source = []
#     if res['venue'] != None:
#         source.append(to_tag(res['venue'], 'semantic'))
#     if 'affiliations' in res['authors']:
#         source.append(to_tag(res['authors']['affiliations'], 'semantic'))
#     if source == []:
#         source.append('semantic')
#     for x in source:
#         paper['source'].append({"name": x})
    ##### - open_source
    open_source = paper["abstract"].find('https://')
    if open_source != -1:
        paper["code"] = paper["abstract"][open_source:-1]
    else:
        paper["code"] = ''
    ##### - authors
    paper['authors'] = []
    for au in res['authors']:
        paper['authors'].append(au['name'])
    paper['authors'] = ', '.join(paper['authors'])
    ##### - year
    paper['date'] = str(res['year']) + "-01-01"
    ##### - tldr
    paper['tldr'] = res['tldr'] if (res['tldr']!=None) else {'text': ''}
    ##### - references
    if res['references'] != None:
        paper['references'] = res['references']
    return paper


def search_semantic(title: str, max_search=10):
    print('Searching in Semantic ...\n')
    paper = {}
    target = title_strip(title)
    search_url = get_search_url('semantic', max_search, title)
    try:
        ress = urllib.request.urlopen(search_url).read()
        ress = json.loads(ress)['data']
    except:
        raise RuntimeError('Connection failed in Semantic.')
    try: 
        for i in range(max_search):
            res = ress[i]
            if title_strip(res['title']) == target:
                # unzip paper data from response
                ## 1 basic info
                paper['paperId'] = res['paperId']
                paper['title'] = res['title']
                paper['url'] = res['url']
                ## 2 externalIds
                res = res['externalIds']
                paper['DOI'] = res['DOI'] if ('DOI' in res) else ''
                paper['ArXiv'] = res['ArXiv'] if ('ArXiv' in res) else ''
                paper = semantic_details(paper)
                return paper
        raise LookupError('Paper Not Found in Semantic. ' + search_url)
    except:
        raise LookupError('No Search Results presented. ' + search_url)


def search_arxiv(title: str, max_result=10):
    print('Searching in arxiv ...\n')
    paper = {}
    target = title_strip(title)
    search_url = get_search_url('arxiv', max_result, title)
    try:
        # get paper data from search
        res = urllib.request.urlopen(search_url).read()
        res = parseString(res)
        feed = res.childNodes[0]
        entries = feed.getElementsByTagName('entry')
    except:
        raise RuntimeError('Connection failed in Arxiv.')
    
    for i in range(max_result):
        entry = entries[i]
        if title_strip(entry.getElementsByTagName('title')[0].childNodes[0].toxml()) == target:
            # insert paper data from entry
            ## authors
            author_ele = entry.getElementsByTagName('author')
            authors = []
            for au in author_ele:
                authors.append(au.getElementsByTagName('name')[0].childNodes[0].toxml())
            authors = ", ".join(authors)
            ## others
            paper = {"title": entry.getElementsByTagName('title')[0].childNodes[0].toxml() if entry.getElementsByTagName('title') != [] else '',
                     "date": entry.getElementsByTagName('published')[0].childNodes[0].toxml(),
                     "paperId": '',
                     "ArXiv": entry.getElementsByTagName('id')[0].childNodes[0].toxml().split('/abs/')[-1],
                     "DOI":'',
                     "url": entry.getElementsByTagName('link')[0].getAttribute("href"),
                     "abstract": entry.getElementsByTagName('summary')[0].childNodes[0].toxml().replace('\n', ' '),
#                      "source": [{"name": to_tag(entry.getElementsByTagName('arxiv:comment')[0].childNodes[0].toxml())}],
                     "authors": authors,
                     "tldr": {"text": ''},
                     "references": ''}
            open_source = paper["abstract"].find('https://')
            if open_source != -1:
                paper["code"] = paper["abstract"][open_source:-1]
            else:
                paper["code"] = ''
            return paper
    raise LookupError('Paper Not Found in Arxiv. ' + search_url)


def send_notion(paper):
    url = "https://api.notion.com/v1/pages"
    content = {
 # attention: insert your own database_id and replace the "please_input_your_own_database_id"
        "parent": {"type": "database_id", "database_id": "$YOUR_DATABASE_ID$"},
        "properties": {
            "URL": {"url": paper['url']},
            "Name": {"title": [{"type": "text",
                                "text": {"content": paper['title']}}]},
            "TLDR": {"rich_text": [{"type": "text",
                                    "text": {"content": paper['tldr']['text']}}]},
            "Form": {"type": "select",
                     "select": {"name": "Essay",
                                "color": "purple"}},
            "Published": {"type": "date",
                          "date": {"start": paper['date']}},
#             "Source": {"type": "multi_select",
#                        "multi_select": paper['source']},
            "DOI": {"rich_text": [{"type": "text",
                                   "text": {"content": paper['DOI']}}]},
            "ArXiv": {"rich_text": [{"type": "text",
                                     "text": {"content": paper['ArXiv']}}]},
            "组织/团队/作者": {"rich_text": [{"type": "text",
                                        "text": {"content": paper['authors']}}]},
            "开源代码": {"rich_text": [{"type": "text",
                                    "text": {"content": paper['code']}}]},
            "Location": {"rich_text": [{"type": "text",
                                    "text": {"content": paper['location']}}]},
            "未分类": {"type": "checkbox",
                    "checkbox": True}
        },
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": paper['abstract']}}]
                }
            }
        ]
    }
    headers = {
        "Accept": "application/json",
        "Notion-Version": "2022-02-22",
        "Content-Type": "application/json",
   # attention: please replace it with your own notionAPI robot ID
        "Authorization": "$YOUR_INTEGRATION_TOKEN$"
    }
    response = requests.request("POST", url, json=content, headers=headers)
    if response.status_code != 200:
        raise BaseException(response.text)
    return response.text


def main():
    try:
        paper = search_semantic(sys.argv[1])
#         paper = search_semantic("IntraQ: Learning Synthetic Images with Intra-Class Heterogeneity for Zero-Shot Network Quantization")
    except:
        paper = search_arxiv(sys.argv[1])
#         paper = search_arxiv("IntraQ: Learning Synthetic Images with Intra-Class Heterogeneity for Zero-Shot Network Quantization")
    print('Search Finished: ', paper['title'], '\n')
    if paper['ArXiv'] != '':
        try: 
            paper_download_url = "https://arxiv.org/pdf/" + paper['ArXiv'] + ".pdf"
            filepath = sys.argv[2]
            filename = paper['ArXiv'] + '.pdf'
            paper['location'] = os.path.join(filepath, filename)
            urllib.request.urlretrieve(paper_download_url, paper['location'])
            print('Paper Downloaded.\n')
        except:
            paper['location'] = ''
    else:
        paper['location'] = ''
    res = send_notion(paper)
    print('Paper Archived.\n')
    input("Press <enter>")
    return 0


if __name__ == '__main__':
    main()
    #search_semantic("SAGA-Net: efficient pointcloud completion with shape-assisted graph attention neural network")
