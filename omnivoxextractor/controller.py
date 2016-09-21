import os
import wx
from Queue import Queue
from view import LoginFrame, OptionsFrame, DownloadFrame 
from model import MarianopolisAccount, AuthenticationError, HostOS
from threading import Thread, Event
import wx.lib.pubsub.setupkwargs
from wx.lib.pubsub import pub 

class Controller(object):
    
    def __init__(self, app):
        self.account = MarianopolisAccount()
        self.loginview = LoginFrame()
        self.optionsview = OptionsFrame()
        self.downloadview = DownloadFrame()
        self.event = Event()
        self.stop_event = Event()
        self.queue = Queue()
        self.InitLoginView()
        self.InitOptionsView()
        self.InitDownloadView()
        self.InitUI()
        
    def InitUI(self):
        self.loginview.Show()

    def InitLoginView(self):
        self.loginview.loginbutton.Bind(wx.EVT_BUTTON, self.start_login_thread)
        loginId = wx.NewId()
        self.loginview.Bind(wx.EVT_MENU, self.start_login_thread, id=loginId)
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_RETURN, loginId)])
        self.loginview.SetAcceleratorTable(accel_tbl)
        pub.subscribe(self.set_default_progress_bar, "document_count")
        pub.subscribe(self.update_progress_bar, "document_counter")
        pub.subscribe(self.Login, "login_status")
        pub.subscribe(self.set_options, "options")
        pub.subscribe(self.update_download_status, "download_status")
        pub.subscribe(self.complete_download_status, "complete_status")

    def InitOptionsView(self):
        self.optionsview.logoutbutton.Bind(wx.EVT_BUTTON, self.Logout)
        self.optionsview.nextbutton.Bind(wx.EVT_BUTTON, self.Download)

    def InitDownloadView(self):
        self.downloadview.pausebutton.Bind(wx.EVT_BUTTON, self.PauseDownload)
        self.downloadview.logoutbutton.Bind(wx.EVT_BUTTON, self.Logout)
        self.downloadview.optionbutton.Bind(wx.EVT_BUTTON, self.ChangeOptions)

    def start_login_thread(self, evt):
        self.loginview.Disable()
        username = self.loginview.username.GetValue()
        password = self.loginview.password.GetValue()
        thread = LoginThread(self.account, username, password) 
        thread.start()

    def set_options(self, year, semester, year_choices, semester_choices):
        self.optionsview.SetDirectory(os.getcwd())
        self.optionsview.SetSemesterBoxChoices(semester_choices)
        self.optionsview.SetYearBoxChoices(year_choices)
        self.optionsview.SetDefaultYearValue(year)
        self.optionsview.SetDefaultSemesterValue(semester)
    
    def set_default_progress_bar(self, count):
        self.downloadview.SetDefaultProgressBar(count)   

    def update_progress_bar(self, counter):
        self.downloadview.UpdateProgressBar(counter)

    def update_download_status(self, message):
        self.downloadview.StatusUpdate(message)

    def complete_download_status(self): 
        self.downloadview.statustext.SetLabel("Download Completed")
        self.downloadview.pausebutton.Disable()
        self.downloadview.closebutton.Enable()
        self.downloadview.optionbutton.Enable()
        self.downloadview.logoutbutton.Enable()

    def Login(self, status):
        if status == "OK":
            thread = SetOptionsThread(self.account) 
            thread.start()
            thread.join()
            self.loginview.Hide()
            self.optionsview.Show()

        if status == "AuthenticationError":
            self.loginview.ShowErrorMsg("Invalid username or password")
            self.loginview.ClearPasswordBox()
            self.loginview.Enable()
            self.loginview.password.SetFocus()

        if status == "ConnectionError":
            self.loginview.ShowErrorMsg("A connection problem has occured")
            self.loginview.Enable()
    
    def Download(self, evt):
        self.optionsview.Hide()
        self.downloadview.ClearStatus()
        self.downloadview.Show() 
        self.downloadview.Centre()
        self.downloadview.statustext.SetLabel("Downloading...")
        self.downloadview.pausebutton.Enable()
        self.ResumeDownload()

        semester = self.optionsview.semesterbox.GetValue()
        year = self.optionsview.yearbox.GetValue()
        destination = self.optionsview.directorypath.GetValue()

        if not hasattr(self, "downloadmanager"):
            self.downloadmanager = DownloadManager(self.queue)
            self.downloadmanager.start()

        downloadthread = DownloadThread(self.account, year, 
            semester, destination, self.event, self.stop_event)
        self.queue.put(downloadthread)

    def PauseDownload(self, evt):
        self.event.clear()
        self.downloadview.pausebutton.Bind(wx.EVT_BUTTON,
            self.ResumeDownloadEvent)
        self.downloadview.ChangePauseLabel("Resume")
        self.downloadview.closebutton.Enable()
        self.downloadview.optionbutton.Enable()
        self.downloadview.logoutbutton.Enable()

    def ResumeDownloadEvent(self, evt):
        self.ResumeDownload()
    
    def ResumeDownload(self):
        self.event.set()
        self.stop_event.set()
        self.downloadview.pausebutton.Bind(wx.EVT_BUTTON, self.PauseDownload)
        self.downloadview.ChangePauseLabel("Pause")
        self.downloadview.closebutton.Disable()
        self.downloadview.optionbutton.Disable()
        self.downloadview.logoutbutton.Disable()
    
    def ChangeOptions(self, evt):
        self.event.set()
        self.stop_event.clear()
        self.downloadview.Hide()
        self.optionsview.Raise()
        self.optionsview.Centre()

    def Logout(self, evt):
        self.event.set()
        self.stop_event.clear()
        self.loginview.ClearPasswordBox()
        self.loginview.Enable()
        self.optionsview.Hide()
        self.downloadview.Hide()
        self.loginview.Raise()
        self.loginview.Centre()
        self.loginview.password.SetFocus()


class SetOptionsThread(Thread):
    
    def __init__(self, account):
        super(SetOptionsThread, self).__init__()
        self.account = account
    
    def run(self):
        semester = self.account.get_current_semester()
        year = self.account.get_current_year()
        year_choices = self.account.get_choices_year(year)
        semester_choices = self.account.get_choices_semester(semester)
        wx.CallAfter(pub.sendMessage, "options", year=year, semester=semester,
            semester_choices=semester_choices, year_choices=year_choices)


class DownloadManager(Thread):
    
    def __init__(self, queue):
        super(DownloadManager, self).__init__()
        self.queue = queue
        self.daemon = True

    def run(self):
        while True:
            thread = self.queue.get()
            thread.start()
            thread.join()
            self.queue.task_done()


class DownloadThread(Thread):

    def __init__(self, account, year, semester, destination, event, stop_event):
        super(DownloadThread, self).__init__()
        self.daemon = True
        self.account = account
        self.year = year
        self.semester_name = semester
        self.destination = destination
        self.event = event
        self.stop_event = stop_event
    
    def run(self):
        self.hostos = HostOS()
        self.hostos.saving_folder = self.destination 
        self.account.set_semester(self.year, self.semester_name)
        self.semester = self.account.semester
        total_count = self.semester.count_documents()
        wx.CallAfter(pub.sendMessage, "document_count", count=total_count)
        self.counter = 0 
        wx.CallAfter(pub.sendMessage, "document_counter", counter=self.counter)
        self.download_semester()

    def download_semester(self):
        for course in self.semester.courses:
            self.hostos.create_folder(course.name)
            for document in course.documents:
                self.event.wait()
                if not self.stop_event.isSet():
                    wx.CallAfter(pub.sendMessage, "document_counter", counter=0)
                    return
                self.download_document(document)
        wx.CallAfter(pub.sendMessage, "complete_status")

    def download_document(self, document):
        if self.hostos.isexisting(document.course, document.name):
            self.update_text(True, document.name, document.course)
        else:
            self.update_text(False, document.name, document.course)
            document.download()
        self.update_counter()
    
    def update_text(self, existing, document_name, course_name):
        status = "Existing" if existing else "Downloading"
        message = "{}-{}-{}".format(status, course_name, document_name)
        wx.CallAfter(pub.sendMessage, "download_status", message=message) 

    def update_counter(self):
        self.counter += 1
        wx.CallAfter(pub.sendMessage, "document_counter", counter=self.counter)

class LoginThread(Thread):

    def __init__(self, account, username, password):
        super(LoginThread, self).__init__()
        self.username = username
        self.password = password
        self.account = account
    
    def run(self):
        try :
            self.account.login(self.username, self.password)
        except AuthenticationError:
            wx.CallAfter(pub.sendMessage, "login_status", 
                status="AuthenticationError")
        except: 
            raise
            wx.CallAfter(pub.sendMessage, "login_status", 
                status="ConnectionError")
        else:
            wx.CallAfter(pub.sendMessage, "login_status",
                status="OK")

if __name__ == '__main__':
    app = wx.App(False)
    controller = Controller(app)
    app.MainLoop()

