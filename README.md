# PaperClipper
输入论文标题，本爬虫将自动在semanticscholar.com和arxiv.com搜索该文章，自动获取其日期、作者、url、摘要等信息，并自动发送到你提前设置好的notion数据库里，同时自动从arxiv下载论文，然后将论文的保存地址在notion页面的address属性中展示。
如果您没有编程基础，请查阅[本CSDN教程](https://blog.csdn.net/Hydius/article/details/132711468?spm=1001.2014.3001.5502)，将有详细的步骤说明。

## 0. Notion Database准备
### 0.0 设置database的属性
在Notion中新建一个database页面，打开我的模板页面并Duplicate到自己的数据库里，或者根据下面的表格手动设置相应的属性。
下面是目前支持爬取的属性(摘要会自动爬取到页面内容中)，请务必保持自己页面含有下面的所有属性，否则会影响爬虫使用。如需改变属性名字，直接在源码中替换修改即可。
|属性名字|属性类别|
|--|--|
|Name|Title|
|URL|URL|
|TLDR|Text|
|Form|Select|
|Published|Date|
|DOI|Text|
|ArXiv|Text|
|组织/团队/作者|Text|
|开源代码|Text|
|Location|Text|
|Confirm|Checkbox|

### 0.1 获取database id
创建以后，在右上角点击Share，并点击Copy link，获取到一串形似以下字符串的链接：

> https://www.notion.so/yourid/d6d2651588e4473e970d53183d585870?v=cc500e0f66364db9841c96d6aa17d473&pvs=4

其中yourid/之后、?v=之前的字符串就是你的这个数据库的id（在本例子中，是d6d2651588e4473e970d53183d585870），请复制并保存下来。

### 0.2 获取integration token
在[My Integrations](https://www.notion.com/my-integrations)中新建一个或者打开已有的Integration，获取该integration的token，记录下来。

### 0.3 连接database到integration
在database页面中，点击右上角的三个点按钮，选择*Add Connection*，找到并选择所需的integration，Confirm。

## 1. 代码准备
你需要将`$YOUR_DATABASE_ID$`更换成数据库id，再将`$YOUR_INTEGRATION_TOKEN$`更换成integration的token。

## 2. main函数的参数和使用
本爬虫的main函数可以接受最少一个，最多两个的额外参数；其中，sys.argv\[1\]将被输入为论文标题进行精确匹配搜索，sys.argv\[2\]将被输入为查找到论文后下载的保存地址。
使用方法是在cmd中输入以下指令：
```
python ./ToNotion.py "Paper Title" "Paper Download Path"
```
## 3. 具体函数的功能介绍
search_semantic和search_arxiv两个函数接收一个字符串作为论文标题，并分别在semantic scholar和arxiv上通过api搜索论文，更改max_search将会改变每次查询到的论文个数，如果查询不到所需论文，可以酌情增大该参数。
send_notion接收一个包含了论文信息的词典，并通过http post方式连接notion的api，在notion上新建页面并更改相应属性；返回值是一个http response，信息发送失败时，将会抛出BaseException。
