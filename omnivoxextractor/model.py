import os
import re
import requests
from time import strftime
from bs4 import BeautifulSoup
from collections import deque, OrderedDict

class AuthenticationError(Exception): pass

class OmnivoxAccount(object):	
    def __init__(self):
        self.session = requests.Session()
        self.semester_ids = OrderedDict([
            ("Winter",'1'), 
            ("Summer",'2'),
            ("Fall",'3')
        ])

    def login(self, username, password):
        if not username:
            raise AuthenticationError()
        self.username = username
	self.password = password
        login_params = {'NoDA':self.username, 'PasswordEtu':self.password}
            
        login_page_html = self.session.get(self.login_url).content
        soup = BeautifulSoup(login_page_html, "html.parser")
        login_params['k'] = soup.find("input", attrs={"name":'k'}).get("value")

        main = self.session.post(self.login_url, data=login_params).content
        soup = BeautifulSoup(main, "html.parser")
        if soup.find_all(class_="PageNonTrouvee"):
            raise AuthenticationError() 
    
    @staticmethod
    def get_current_semester():
        month = int(strftime('%m'))
        if 1 <= month <= 5:
	    return "Winter" 
        if 6 <= month <= 8:
	    return "Summer"
        if 9 <= month <= 12:
	    return "Fall"
   
    def get_choices_semester(self, semester):
        keys = self.semester_ids.keys()
        index = keys.index(semester)
        choices = deque(keys)
        choices.rotate(index*-1)
        return list(choices)

    @staticmethod 
    def get_current_year():
        return strftime('%Y')

    @staticmethod 
    def get_choices_year(year):
        year = int(year)
        end = year - 5
        return map(str, range(year, end, -1))

class MarianopolisAccount(OmnivoxAccount):
    def __init__(self):
        super(MarianopolisAccount, self).__init__()
        self.login_url = ("https://marianopolis.omnivox.ca/"
            "intr/Module/Identification/Login/Login.aspx")

    def set_semester(self, year, semester):
        semester_id = self.semester_ids[semester]
        self.semester = Semester(year, semester_id, self.session)

class Semester(object):
    def __init__(self, year, semester_id, session):
        self.year = year
        self.semester_id = semester_id
        self.session = session
        self.set_courses()
        

    def set_courses(self):
        soup = self.get_list_documents_soup()
        base_url = ("https://www-mpo-lea.omnivox.ca")
        tags = soup.find_all("a", class_ ="DisDoc_Sommaire_NomCours")
        courses = []
        for tag in tags:
            name = tag.get_text(strip=True)
            link = base_url + tag.get('href')
            courses.append(Course(name, link, self.session))
        self.courses = courses
    
    def get_list_documents_soup(self):
        year_fmt = str(self.year)
        semester_fmt = str(self.semester_id)
        base_url = ("https://marianopolis.omnivox.ca/"
            "intr/Module/ServicesExterne/Skytech.aspx")
        params = {"IdServiceSkytech":"Skytech_Omnivox"}
        params["lk"] = ("/ESTD/CVIE?ANSES={0}{1}"
            "&MODULE=DDLE&ITEM=INTRO").format(year_fmt, semester_fmt)
        content = self.session.get(base_url, params=params).content
        return BeautifulSoup(content, "html.parser")

    def download(self):
        for course in self.courses:
            course.download()

    def count_documents(self):
        count = 0
        for course in self.courses:
            count += course.count_documents()
        return count


class Course(object):
    
    def __init__(self, name, link, session):
        self.name = name
        self.link = link
        self.session = session
        self.set_documents()

    def set_documents(self):
        content = self.session.get(self.link).content
        soup = BeautifulSoup(content, "html.parser")
	rows = soup.find_all("td", \
            class_="lblDescriptionDocumentDansListe colVoirTelecharger")
        base_url = "https://www-mpo-lea.omnivox.ca/cvir/ddle/"
        documents = []
        for row in rows:
            doclink = base_url + row.contents[1].get('href')
	    docname = row.contents[1].contents[1].get('title')
            if docname: 
                documents.append(
                    Document(self.name, docname, doclink, self.session))
        self.documents = documents

    def download(self):
        for document in self.documents:
            document.download()

    def count_documents(self):
        return len(self.documents)
        

class Document(object): 
    def __init__(self, course, name, link, session):
        self.course = course
        self.name = name
        self.link = link
        self.session = session

    def download(self):
        result = self.session.get(self.link, stream=True)
        with open(self.name, 'wb') as f:
            for chunk in result.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)


class HostOS(object):

    def __init__(self):
        self.saving_folder = None

    def create_folder(self, course_name):
        course_name = course_name.replace('/', '-')
        path = os.path.join(self.saving_folder, course_name)
	if not os.path.exists(path):	
            os.mkdir(path)
	os.chdir(path)
    
    def isexisting(self, course_name, filename):
        course_name = course_name.replace('/', '-')
        path = os.path.join(self.saving_folder, course_name, filename)
        return os.path.isfile(path)
    
    def current_directory(self):
        return self.saving_folder or os.getcwd()

        
