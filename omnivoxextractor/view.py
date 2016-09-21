import os
import threading
import wx
import wx.lib.pubsub.setupkwargs
from wx.lib.pubsub import pub

class OptionsFrame(wx.Frame):

    def __init__(self):
        super(OptionsFrame, self).__init__(None, title="Mecomni",
            size=(500,300), style=wx.DEFAULT_FRAME_STYLE 
            &~ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX))
        self.InitUI()
        self.Centre()	

    def InitUI(self):
        panel = wx.Panel(self)

        vbox = wx.BoxSizer(wx.VERTICAL)
        fgs = wx.GridBagSizer(7,3)

        optiondestination = wx.StaticText(panel, label="Options")
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD)
        optiondestination.SetFont(font)
        fgs.Add(optiondestination, pos=(0,0))

        folderbox = wx.StaticBox(panel, label="Select Destination Folder:")
        fboxsizer = wx.StaticBoxSizer(folderbox, wx.HORIZONTAL)
        self.directorypath = wx.TextCtrl(panel, style=wx.TE_READONLY)
        fboxsizer.Add(self.directorypath, proportion=1, flag=wx.TOP, border=2)
        self.browsebutton = wx.Button(panel, label='Browse...')
        fboxsizer.Add(self.browsebutton, flag=wx.ALIGN_RIGHT)
        self.browsebutton.Bind(wx.EVT_BUTTON, self.browse)
        fgs.Add(fboxsizer, pos=(1,0), flag=wx.TOP|wx.EXPAND, span=(1,3),
            border=10)
        fgs.AddGrowableCol(0)

        sessionbox = wx.StaticBox(panel, label="Semester:")
        sboxsizer = wx.StaticBoxSizer(sessionbox, wx.HORIZONTAL)
        self.semesterbox = wx.ComboBox(panel, style=wx.CB_READONLY)
        sboxsizer.Add(self.semesterbox)
        self.yearbox = wx.ComboBox(panel, style=wx.CB_READONLY)
        sboxsizer.Add(self.yearbox, flag=wx.ALIGN_RIGHT)
        fgs.Add(sboxsizer,pos=(2,0), flag=wx.EXPAND, span=(1,3))

        line = wx.StaticLine(panel)
        fgs.Add(line, pos=(5,0), flag=wx.EXPAND, span=(1,3))
        fgs.AddGrowableRow(4)

        self.logoutbutton = wx.Button(panel, label='Logout')
        fgs.Add(self.logoutbutton, pos=(6,0), flag=wx.LEFT)

        self.nextbutton = wx.Button(panel, label='Download')
        fgs.Add(self.nextbutton, pos=(6,1), flag=wx.LEFT, border=150)

        closebutton = wx.Button(panel, label='Close')
        fgs.Add(closebutton,pos=(6,2), flag=wx.ALIGN_RIGHT)
        closebutton.Bind(wx.EVT_BUTTON, self.closeframe)	

        self.Bind(wx.EVT_CLOSE, self.closeframe)
        vbox.Add(fgs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizer(vbox)

    def SetDefaultSemesterValue(self, semester):
        self.semesterbox.SetValue(semester)

    def SetSemesterBoxChoices(self, choices):
        self.semesterbox.SetItems(choices)

    def SetDefaultYearValue(self, year):
        self.yearbox.SetValue(year)
    
    def SetYearBoxChoices(self, choices):
        self.yearbox.SetItems(choices)
        
    def SetDirectory(self, directory):
        self.directorypath.SetValue(directory)

    def browse(self, evt):
        openfolderdialog = wx.DirDialog(self)
        openfolderdialog.ShowModal()
        if openfolderdialog.GetPath():
            self.directorypath.SetValue(openfolderdialog.GetPath())

    def initiatedownload(self, evt):
        self.Disable()
        self.Hide()
        DownloadFrame().Show()	

    def logout(self, evt):
        self.Hide()
        mainaccount.logout()
        LoginFrame().Show()		
        
    def closeframe(self, evt):
        wx.Exit()

class LoginFrame(wx.Frame):

    def __init__(self):
        super(LoginFrame, self).__init__(None, title='Mecomni', size=(400,200),
            style=wx.DEFAULT_FRAME_STYLE &~ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX))
        self.InitUI()
        self.Centre()  

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        fgs = wx.GridBagSizer(4,3)

        heading = wx.StaticText(panel, label='Omnivox Login')
        font = wx.Font(18, wx.FONTFAMILY_DECORATIVE,
            wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        heading.SetFont(font)
        fgs.Add(heading, pos=(0,0), flag=wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM,
            border=20, span=(1,3))

        usertext = wx.StaticText(panel, label='Username:')
        fgs.Add(usertext, pos=(1,0), border=10, 
            flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.BOTTOM)
        passtext = wx.StaticText(panel, label='Password:')
        fgs.Add(passtext, pos=(2,0), border=10,
            flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
        self.username = wx.TextCtrl(panel)
        fgs.Add(self.username, pos=(1,1), flag=wx.EXPAND|wx.BOTTOM,
            border=10, span=(1,2))
        self.password = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        fgs.Add(self.password, pos=(2,1), flag=wx.EXPAND, span=(1,2))		
        fgs.AddGrowableCol(1)

        self.loginbutton = wx.Button(panel, label="Login") 
        fgs.Add(self.loginbutton, pos=(3,2), 
            flag=wx.ALIGN_RIGHT|wx.TOP, border=7)
        loginId = wx.NewId()
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_RETURN, loginId)])
        self.SetAcceleratorTable(accel_tbl)

        self.Bind(wx.EVT_CLOSE, self.closeframe)
        panel.SetFocus()
        vbox.Add(fgs, 1, wx.ALL|wx.EXPAND, 10)
        panel.SetSizer(vbox)

    def ClearPasswordBox(self):
        self.password.SetValue('') 

    def ShowErrorMsg(self, message):
        error_dialog = wx.MessageDialog(None, message, 'Error',
            wx.OK | wx.ICON_ERROR)
        error_dialog.Center()
        error_dialog.ShowModal()

    def closeframe(self, evt):
        wx.Exit()

class DownloadFrame(wx.Frame):

    def __init__(self):
        super(DownloadFrame, self).__init__(None, title='Mecomni', 
            size=(500,300), style=wx.DEFAULT_FRAME_STYLE &~ 
            (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX))
        self.InitUI()
        self.Centre()

    def InitUI(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        fgs = wx.GridBagSizer(4,4)	

        self.statustext = wx.StaticText(panel,label='Downloading...')
        fgs.Add(self.statustext, pos=(0,0))

        self.gauge = wx.Gauge(panel)
        fgs.Add(self.gauge, pos=(1,0),flag=wx.LEFT|wx.EXPAND,span=(1,4))

        self.statusbox = wx.ListBox(panel)
        fgs.Add(self.statusbox, pos=(2,0), flag=wx.EXPAND, span=(1,4))

        fgs.AddGrowableCol(0)
        fgs.AddGrowableRow(2)

        self.closebutton = wx.Button(panel, label='Close')
        fgs.Add(self.closebutton, pos=(3,3))
        self.closebutton.Disable()
        self.closebutton.Bind(wx.EVT_BUTTON, self.closeframe)

        self.logoutbutton = wx.Button(panel, label='Logout')
        self.logoutbutton.Disable()
        fgs.Add(self.logoutbutton, pos=(3,0))

        self.optionbutton = wx.Button(panel, label='Options')
        self.optionbutton.Disable()
        fgs.Add(self.optionbutton, pos=(3,1))

        self.pausebutton = wx.Button(panel, label='Pause')
        fgs.Add(self.pausebutton, pos=(3,2))

        self.Bind(wx.EVT_CLOSE, self.closeframe)
        vbox.Add(fgs, 1, wx.ALL|wx.EXPAND, 10)	
        panel.SetSizer(vbox)

    def SetDefaultProgressBar(self, count):
        self.gauge.SetRange(count)

    def UpdateProgressBar(self, counter):
        self.gauge.SetValue(counter)

    def UpdateEndDownload(self):
        self.statustext.SetLabel('Download Completed')
        self.downloadthread.join()
        self.closebutton.Enable()
        self.optionbutton.Enable()
        self.logoutbutton.Enable()
        self.pausebutton.Disable()

    def ChangePauseLabel(self, message):
        self.pausebutton.SetLabel(message)

    def StatusUpdate(self, message):
        self.statusbox.Append(message)
        self.statusbox.SetSelection(self.statusbox.GetCount()-1)

    def ClearStatus(self):
        self.statusbox.Clear()

    def closeframe(self, evt):
        wx.Exit()
