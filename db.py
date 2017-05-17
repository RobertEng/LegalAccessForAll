import MySQLdb
import csv
from bs4 import BeautifulSoup

csvfile = open('CA_statutes.csv', 'wb')
writer = csv.writer(csvfile)


db = MySQLdb.connect(host="localhost", user="root", passwd="ubuntu", db="capublic")
cur = db.cursor(MySQLdb.cursors.DictCursor)

cur.execute("SELECT * FROM law_section_tbl")
results = cur.fetchall()

def get_name(id, law_code):
    cur.execute("SELECT * FROM law_toc_sections_tbl WHERE id = %s", (id, ))
    tree = cur.fetchone()['node_treepath']
    paths = tree.split(".")
    name = []
    for i in range(1, len(paths) + 1):
        path = ".".join(paths[0:i])
        cur.execute("SELECT heading FROM law_toc_tbl WHERE law_code = %s AND node_treepath = %s", (law_code, path))
        heading = cur.fetchone()['heading']
        name.append(heading)

    return name

def storeStatuteCSV(title, name_lst, text):
    #with open('CA_statutes.csv', 'wb') as csvfile:
    global writer

    # Format everything so we don't have ugly unicode symbols. >:(
    try:
        title = title.encode('ascii', 'ignore')
    except:
        pass
    new_name_lst = []
    for string in name_lst:
        try:
            new_str = string.encode('ascii', 'ignore')
        except:
            new_str = string
        new_name_lst.append(new_str)
    try:
        text = text.encode('ascii', 'ignore')
    except:
        pass

    writer.writerow([title] + new_name_lst + [text])

        
print "{0} statutes".format(len(results))
i = 0
for law in results:
    id = law['id']
    print i
    i += 1
    law_code = law['law_code']
    section_num = law['section_num']
    try:
        name = get_name(id, law_code)
    except:
        name = []
    content = law['content_xml']
    text = BeautifulSoup(content, "html.parser").get_text()
    storeStatuteCSV(section_num, name, text)
