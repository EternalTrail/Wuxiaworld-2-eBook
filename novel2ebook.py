import sys, inspect
import NovelParsers
from NovelDownloader import NovelDownloader
from TKWrapper import TKWrapper
import threading
import uuid

class NovelGUI:
    
    def __init__(self):
        
        # Create an instance of the Tkinter wrapper and novel website parsers
        self.TKW = TKWrapper("Novel 2 E-Book", 700, 340, "favicon.ico")
        self.parsers = [parser() for name, parser in inspect.getmembers(NovelParsers, inspect.isclass) if parser.__module__ == 'NovelParsers']
        self.coverSize = (210,300)
        
        # Get the book names and select which parser to use
        self.selectedParser = None
        novels = []
        for parser in self.parsers:
            novels.extend(parser.getNovelNames())
        novels.sort()
        self.selectParser(novels[0])
        
        # Create all UI elements
        self.TKW.createLabel("NovelLabel", "Select Novel: ", 0, {"pady":10, "padx":10, "sticky":"W"})
        self.TKW.createLabel("BookLabel", "Select Book: ", 0, {"pady":10, "padx":10, "sticky":"W"})
        self.TKW.createLabel("EndLabel", "Select Ending Chapter: ", 0, {"pady":10, "padx":10, "sticky":"W"})
        self.TKW.createLabel("ChaptersOnlyLabel", "Download separate chapters: ", 0, {"pady":10, "padx":10, "sticky":"W"})
        self.TKW.createCombobox("NovelCombobox", 1, novels, {"width":42})
        self.TKW.createCombobox("BookCombobox", 1, self.selectedParser.getNovelBookNames(novels[0]), {"width":42})
        self.TKW.createCombobox("EndCombobox", 1, self.selectedParser.getNovelBookNames(novels[0]), {"width":42})
        self.TKW.guiElements["EndCombobox"][1].configure(state="disabled")
        self.TKW.createCheckbutton("ChaptersOnly", 1, {"command":self.onChapterCheckboxChange}, {"sticky":"W", "padx":20})
        self.TKW.decrementRow(1)
        self.TKW.createButton("DownloadButton", "Download", 1, {"command":self.onDownloadButtonClick})
        self.TKW.decrementRow(1)
        self.TKW.createButton("CancelButton", "Cancel", 1, {"command":self.onCancelButtonClick}, {"sticky":"E"})
        self.stopDownload = False
        
        # Attach functions after creating the comboboxes to prevent errors on startup
        self.TKW.guiElements["NovelCombobox"][0].trace("w", self.onNovelFieldChange)
        self.TKW.guiElements["BookCombobox"][0].trace("w", self.onBookFieldChange)
        
        # Insert the cover image of the first book on WW
        self.coverImage = self.selectedParser.getImagePillow(novels[0])
        self.coverImage.thumbnail(self.coverSize)
        self.TKW.insertImage("CoverImage", self.coverImage, 3, {"sticky":"W", "pady":20, "padx":20, "rowspan":20})
        
        self.TKW.incrementRow(0)
        self.TKW.createProgressbar("ProgressBar", 0, {"length":440}, {"columnspan":2, "pady":50, "sticky":"E"})
        self.progressTrack = 0
        self.progressTrackID = None
        
        # Set download pool size (how many chapters to download at a time)
        self.poolSize = 40
        
        # Set the update interval
        self.updateInterval = 100
        self.updateGUI()
        
        # Launch the GUI
        self.TKW.begin()
    
    
    def selectParser(self, novel):
        
        # Check which parser the novel comes from select that parser
        for parser in self.parsers:
            if novel in parser.getNovelNames():
                self.selectedParser = parser
                break
    
    
    def onNovelFieldChange(self, index, value, op):
        
        # Get the selected novel name and replace the image accordingly
        novel = self.TKW.guiElements["NovelCombobox"][0].get()
        
        # Figure out which parser to use
        self.selectParser(novel)
        self.coverImage = self.selectedParser.getImagePillow(novel)
        self.coverImage.thumbnail(self.coverSize)
        self.TKW.replaceImage("CoverImage", self.coverImage)
        
        # Set the values of the comboboxes to either the chapters or the books
        if self.TKW.guiElements["ChaptersOnly"][0].get():
            self.TKW.guiElements["BookCombobox"][1]["values"] = list(dict.fromkeys(self.selectedParser.getNovelChapterNames(novel)))
            self.TKW.guiElements["EndCombobox"][1]["values"] = list(dict.fromkeys(self.selectedParser.getNovelChapterNames(novel)))
        else:   
            self.TKW.guiElements["BookCombobox"][1]["values"] = self.selectedParser.getNovelBookNames(novel)
        
        # Set the selected items in both comboboxes to the first element
        self.TKW.guiElements["BookCombobox"][1].current(0)
        self.TKW.guiElements["EndCombobox"][1].current(0)
        
    
    
    def onBookFieldChange(self, index, value, op):
        
        # If the checkbutton is checked, make sure that the end chapter is always
        # after the starting chapter
        if self.TKW.guiElements["ChaptersOnly"][0].get():
            novel = self.TKW.guiElements["NovelCombobox"][0].get()
            chapterList = list(dict.fromkeys(self.selectedParser.getNovelChapterNames(novel)))
            chapIndex = chapterList.index(self.TKW.guiElements["BookCombobox"][0].get())
            
            if self.TKW.guiElements["EndCombobox"][0].get() in chapterList:
                endChapIndex = chapterList.index(self.TKW.guiElements["EndCombobox"][0].get())
            else: 
                endChapIndex = chapIndex
            
            if chapIndex+1 < len(chapterList):
                self.TKW.guiElements["EndCombobox"][1]["values"] = chapterList[chapIndex:]
            else:
                self.TKW.guiElements["EndCombobox"][1]["values"] = [chapterList[-1]]
            
            if chapIndex < endChapIndex-1:
                self.TKW.guiElements["EndCombobox"][1].current(endChapIndex-chapIndex)
            else:
                self.TKW.guiElements["EndCombobox"][1].current(0)
        
    
    
    def onChapterCheckboxChange(self):
        
        # When the checkbutton is clicked, set the values of the comboboxes accordingly
        novel = self.TKW.guiElements["NovelCombobox"][0].get()
        if self.TKW.guiElements["ChaptersOnly"][0].get():
            self.TKW.guiElements["BookLabel"]['text'] = 'Select Starting Chapter:'
            self.TKW.guiElements["EndCombobox"][1].configure(state = "readonly")
            
            self.TKW.guiElements["BookCombobox"][1]["values"] = list(dict.fromkeys(self.selectedParser.getNovelChapterNames(novel)))
            self.TKW.guiElements["EndCombobox"][1]["values"] = list(dict.fromkeys(self.selectedParser.getNovelChapterNames(novel)))
        else:
            self.TKW.guiElements["BookLabel"]['text'] = 'Select Book:'
            self.TKW.guiElements["BookCombobox"][1]["values"] = self.selectedParser.getNovelBookNames(novel)
            self.TKW.guiElements["EndCombobox"][1].configure(state = "disabled")
        self.TKW.guiElements["BookCombobox"][1].current(0)
        self.TKW.guiElements["EndCombobox"][1].current(0)
        
    
    def updateProgresstrack(self, id):
        
        if id != self.progressTrackID:
            return True
        if self.stopDownload == True:
            self.progressTrack = 0
            return True
        else:
            self.progressTrack += 1
            return False
        
    def updateGUI(self):
        self.TKW.guiElements["ProgressBar"]['value']=self.progressTrack
        self.TKW.app.after(self.updateInterval, self.updateGUI)
        #self.TKW.app.update()
    
    def onCancelButtonClick(self):
        
        self.progressTrackID = uuid.uuid1()
        self.stopDownload = True
    
    
    def onDownloadButtonClick(self):
        
        # When the download button is clicked, download the book or the chapters
        # depending on the checkbutton state
        novel = self.TKW.guiElements["NovelCombobox"][0].get()
        self.progressTrack = 0
        self.stopDownload = False
        self.progressTrackID = uuid.uuid1()
        if self.TKW.guiElements["ChaptersOnly"][0].get():
            chapterList = list(dict.fromkeys(self.selectedParser.getNovelChapterNames(novel)))
            startChapter = chapterList.index(self.TKW.guiElements["BookCombobox"][0].get())
            endChapter = chapterList.index(self.TKW.guiElements["EndCombobox"][0].get())
            self.TKW.guiElements["ProgressBar"].config(mode="determinate", maximum = endChapter-startChapter+1, value = 0)
            self.newThread = threading.Thread(target=NovelDownloader.generateBookFromToMulti, args=(self.selectedParser,\
                                              novel, startChapter, endChapter), kwargs={"callback":self.updateProgresstrack,\
                                              "poolSize":self.poolSize, "idnum":self.progressTrackID})
            self.newThread.start()
            #NovelDownloader.generateBookFromToMulti(self.selectedParser, novel, startChapter, endChapter, callback = self.updateProgresstrack)
        else:
            chapterList = self.selectedParser.getNovelBookChapterLinks(novel, self.TKW.guiElements["BookCombobox"][0].get())
            self.TKW.guiElements["ProgressBar"].config(mode="determinate", maximum = len(chapterList), value = 0)
            self.newThread = threading.Thread(target=NovelDownloader.generateBookMulti, args=(self.selectedParser,\
                                              novel, self.TKW.guiElements["BookCombobox"][0].get()), kwargs={"callback":self.updateProgresstrack,\
                                              "poolSize":self.poolSize, "idnum":self.progressTrackID})
            self.newThread.start()
            #NovelDownloader.generateBook(self.selectedParser, novel, self.TKW.guiElements["BookCombobox"][0].get(), callback = self.updateProgresstrack)
    
    
if __name__ == "__main__":
    NovelGUI()