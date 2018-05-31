from tkinter import *
from tkinter import messagebox
from bs4 import BeautifulSoup
import urllib.request

treeStack = list()
cur_depth = 0
GITHUB_URL = 'https://github.com'

# cur_depth 0 -> 아무것도 검색하지 않은 상태
# cur_depth 1 -> repository
# cur_depth 2+++ -> file, folders
# tree / blob 이 폴더와 파일을 구분하는 키워드이며 이것은 url.split 5번 인덱스


def clear_tree():
    docTree.delete(0, END)
    typeTree.delete(0, END)


def get_html(url):
    try:
        page = urllib.request.urlopen(url)
        html = page.read()
        page.close()
        return html
    except urllib.request.HTTPError:
        return None


def git_repository_search(*event):
    global docTree, cur_depth, gitIDEntry, GITHUB_URL
    clear_tree()
    if gitIDEntry.get() == "":
        messagebox.showwarning("ID 입력", "GitHub ID를 입력하세요")
        return
    html = get_html(GITHUB_URL + '/' + gitIDEntry.get() + "?tab=repositories")
    if html is None:
        messagebox.showerror("GItHub URL Error", "해당 아이디는 존재하지 않습니다.")
        return
    soup = BeautifulSoup(html, 'html.parser')
    count = soup.find(title='Repositories')
    if count is None:
        docTree.insert('end', 'Repository 가 존재하지 않습니다.')
        return
    repository_count = int(soup.find(title='Repositories').find('span', class_='Counter').get_text().rstrip().lstrip())
    if repository_count < 1:
        docTree.insert('end', 'Repository 가 존재하지 않습니다.')
    else:
        rep_dict = dict()
        rep_list = soup.find('div', id='user-repositories-list').select('ul > li')
        for i in range(len(rep_list)):
            name = rep_list[i].select('h3')[0].get_text().rstrip().lstrip()
            rep_dict[name] = GITHUB_URL + rep_list[i].select('h3 > a')[0]['href']
            docTree.insert('end', name)
            typeTree.insert('end', 'REPOSITORY')
        treeStack.append(rep_dict)
        cur_depth += 1


def take_to_next_level(row_type, url):
    global cur_depth, treeStack, sourceText
    if row_type == 'Repository' or row_type == 'Folder':
        html = get_html(url)
        if html is None:
            messagebox.showerror("GItHub URL Error", "잘못된 경로입니다.")
            return
        soup = BeautifulSoup(html, 'html.parser')
        soup = soup.select('tr.js-navigation-item > td.content > span > a')
        tree_dict = dict()
        for listItem in soup:
            new_name = listItem.get_text()
            new_url = GITHUB_URL + listItem['href']
            tree_dict[new_name] = new_url
        treeStack.append(tree_dict)
        cur_depth += 1
    elif row_type == 'File':
        html = get_html(url)
        if html is None:
            messagebox.showerror("GItHub URL Error", "잘못된 경로입니다.")
            return
        sourceText.config(state=NORMAL)
        soup = BeautifulSoup(html, 'html.parser')
        soup = soup.select('table.js-file-line-container')
        sourceText.delete('1.0', END)
        if len(soup) < 1:
            sourceText.insert(END, "This is raw file.")
        else:
            soup = soup[0]
            sourceText.insert(END, soup.get_text().replace("\n\n\n\n", "\n"))
        sourceText.config(state=DISABLED)


def take_to_prev_level(*args):
    global cur_depth, treeStack
    if cur_depth < 2:
        return
    cur_depth -= 1
    treeStack.pop()
    refresh_list_view()


def refresh_list_view():
    global treeStack, typeTree
    clear_tree()
    tree_dict = treeStack[-1]
    for name in tree_dict.keys():
        docTree.insert('end', name)
        split = tree_dict[name].split('/')
        if len(split) < 6:
            typeTree.insert('end', 'REPOSITORY')
        elif split[5] == 'tree':
            typeTree.insert('end', 'FOLDER')
        elif split[5] == 'blob':
            typeTree.insert('end', 'FILE')


def listbox_double_clicked(*event):
    global docTree, cur_depth
    if cur_depth < 1:
        return
    name = docTree.selection_get()
    url = treeStack[-1][name]
    row_type = ''
    split = url.split('/')

    if len(split) < 6:  # rep
        row_type = 'Repository'
    elif split[5] == 'tree':    # folder
        row_type = 'Folder'
    elif split[5] == 'blob':    # file
        row_type = 'File'
    take_to_next_level(row_type, url)
    refresh_list_view()


# file, folder - soup.select('tr.js-navigation-item > td.content')
rootWindow = Tk()
rootWindow.geometry('1680x720')
rootWindow.title('GitHub Explorer')

leftFrame = Frame(rootWindow, borderwidth=2, relief='groove')
rightFrame = Frame(rootWindow, borderwidth=2, relief='groove')

# left frame

# Text Label
Label(leftFrame, text='GitHub ID').grid(row=0, column=0, padx=10)
# ID Entry
gitIDEntry = Entry(leftFrame)
gitIDEntry.bind("<Return>", git_repository_search)
gitIDEntry.grid(row=0, column=1)
# Search Button
Button(leftFrame, text='Repository Search', command=git_repository_search).grid(row=0, column=2, padx=10)
# back button
Button(leftFrame, text='Back', command=take_to_prev_level).grid(row=1, column=0, padx=10)
# TreeView
docTree = Listbox(leftFrame)
docTree.grid(row=2, column=0, columnspan=2, sticky=W+E+S+N)
docTree.bind('<Double-1>', listbox_double_clicked)
# Type listbox
typeTree = Listbox(leftFrame)
typeTree.grid(row=2, column=2, sticky=W+E+S+N)
# Frame configure setting
leftFrame.grid_columnconfigure(0, weight=2)
leftFrame.grid_columnconfigure(1, weight=3)
leftFrame.grid_columnconfigure(2, weight=2)
leftFrame.rowconfigure(0, weight=1)
leftFrame.rowconfigure(1, weight=1)
leftFrame.rowconfigure(2, weight=10)
leftFrame.grid(row=0, column=0, sticky=W+E+S+N)

# right frame
Label(rightFrame, text='Source Code').pack()
sourceText = Text(rightFrame)
# sourceText.config(state='disabled')
sourceText.pack(fill=BOTH, expand=1)
rightFrame.grid(row=0, column=1, sticky=W+E+S+N)

# configure root window
rootWindow.grid_columnconfigure(0, weight=1)
rootWindow.grid_columnconfigure(1, weight=1)
rootWindow.rowconfigure(0, weight=1)
gitIDEntry.focus_force()
docTree.insert('end', 'Repository 목록')

# html = getHTML('https://github.com/jungmintaeng?tab=repositories')

rootWindow.mainloop()

