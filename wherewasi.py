import tkinter as Tk
import tkinter.ttk as Ttk
# Pull from 
from TkinterMapView.tkintermapview import TkinterMapView
from tkinter import messagebox
from tkcalendar import Calendar
import configparser
from googletimeline import googletimeline
import query

class WhereAmI(Ttk.Frame):
      
  def __init__(self):
    super().__init__()
    self.WHEREWASI_INI = 'wherewasi.ini'
    self.targetMarker = None
    # Loading all predefined values
    self.config = configparser.ConfigParser()    
    self.config.read(self.WHEREWASI_INI)
    self.SearchTextVar = Tk.StringVar(value = self.config['DEFAULT'].get('lastsearch'))
    self.locations = [ l for l in self.config["LOCATIONS"] if googletimeline.parseLatLng(self.config["LOCATIONS"][l]) is not None ]
    try:
      self.gtimeline = googletimeline(self.config['DEFAULT'].get('googletimeline', 'Timeline.json'))
    except Exception as e:
      self.master.destroy()
      messagebox.showerror('Error', f'Unable to start due to {e}')
    else:
      # Start the GUI if no error found
      self.initUI()
      
  def initUI(self):
    self.master.title('Where was I')
    self.master.geometry(self.config['DEFAULT'].get('geometry',f'{800}x{600}'))
    self.master.protocol('WM_DELETE_WINDOW', self.onWinExit)
    self.win_size = 0
    self.master.bind("<Configure>", self.onWinResize)
    self.pack(fill=Tk.BOTH, expand=True)
    
    searchPanel = Ttk.Frame(self, height=50)
    searchButton = Ttk.Button(searchPanel, text = 'Search', command=self.searchLocation)
    searchButton.pack(side=Tk.RIGHT, padx=5, pady=5)
    self.predefinedLocation = Tk.StringVar() 
    predefinedLocations =  Ttk.OptionMenu(searchPanel, self.predefinedLocation, *self.locations, command=self.usePredefinedLocation) 
    predefinedLocations.pack(side=Tk.LEFT, padx=5, pady=5)   
    locationEntry = Tk.Entry(searchPanel, width=1000, textvariable=self.SearchTextVar)
    locationEntry.pack(side=Tk.LEFT, padx=5, pady=5, fill=Tk.BOTH, expand=True)  
    searchPanel.pack(side=Tk.TOP, fill=Tk.BOTH)
    
    self.searchResult = Ttk.Treeview(self, columns=("Date Time", "Type", "Distance"), show="headings")
    self.searchResult.column(1, width=50, stretch=False)
    self.searchResult.column(2, width=50, stretch=False)
    self.searchResult.bind('<ButtonRelease-1>', self.searchResultSelectItem)
    for col in self.searchResult['columns']:
      self.searchResult.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(self.searchResult, _col, False))
    self.searchResult.pack(side=Tk.RIGHT, fill=Tk.Y)
        
    mapViewPanel = Ttk.Frame(self)
    mapViewPanel.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
    ## Invisible development mode, turn off while doing other thing
    self.mapWidget = TkinterMapView(mapViewPanel)
    self.mapWidget.pack(side=Tk.TOP, fill=Tk.BOTH, expand=True, padx=5, pady=5) 
    #  self.mapWidget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)
    # Use a panel to hold the zoomMap just to add border
    self.zoomMapPanel = Tk.Frame(self, width=300, height=300, border=10)
    self.zoomMapWidget = TkinterMapView(self.zoomMapPanel, corner_radius=10)
    self.zoomMapWidget.pack(fill=Tk.BOTH, expand=True)
  
  def usePredefinedLocation(self, e):
    q = query.query(self.SearchTextVar.get())
    # q.location_name = e
    q.position = self.locationNameToPosition(e)
    self.SearchTextVar.set(q.reform())
  
  def searchLocation(self):
    searchText = self.SearchTextVar.get()
    self.config['DEFAULT']['lastsearch'] = searchText
    q = query.query(searchText)
    results = self.gtimeline.findLocation(q.position, q.distance, q.timefrom, q.timeto)
    self.searchResult.delete(*self.searchResult.get_children())
    if results is not None and len(results) > 0:
      if self.mapWidget is not None:
        self.mapWidget.delete_all_marker()
        self.mapWidget.delete_all_path()
        self.mapWidget.set_position(q.position[0], q.position[1], marker=True, text=q.position, range=q.distance)
        
        self.zoomMapWidget.delete_all_marker()
        self.zoomMapWidget.set_position(q.position[0], q.position[1], marker=True, text=q.position, range=q.distance)
      
      for res in results:
        self.searchResult.insert('', 'end', values=(res.time, res.activity, res.distance, res.timelinepathid))
  
  def searchResultSelectItem(self, item):
    selectedItem = self.searchResult.selection()
    if self.mapWidget is not None:
      self.mapWidget.delete_all_path()
      for result in selectedItem:
        item = self.searchResult.item(result)
        path = self.gtimeline.findPathById(item['values'][3])
        rawpath = [ googletimeline.parseLatLng(x['point']) for x in path ]
        # print(self.searchResult.item(result))
        if len(rawpath) > 0:
          self.mapWidget.set_path(rawpath)
          box = googletimeline.findBoundBox(rawpath)
          self.mapWidget.fit_bounding_box(box[1], box[3])
   
  def onWinExit(self):
    self.config['DEFAULT']['geometry'] = self.master.winfo_geometry()
    with open(self.WHEREWASI_INI, 'w') as configfile:
      self.config.write(configfile) 
    self.master.destroy()      
  
  def onWinResize(self,event):
    x = str(event.widget)
    if x == ".": # . is toplevel window
      if (self.win_size != event.height):
        self.win_size = event.height
        self.zoomMapPanel.place(anchor=Tk.SW, y = event.height - 10, x = 10)
  
  def treeview_sort_column(self, tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(reverse=reverse)
    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l): tv.move(k, '', index)
    # reverse sort next time
    tv.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))
  
  def locationNameToPosition(self, location):
    position = self.config['LOCATIONS'].get(location, '(0,0)')
    return googletimeline.parseLatLng(position)
      
def main():
  root = Tk.Tk()
  root.minsize(1000, 600)
  WhereAmI()
  root.mainloop()  
  
if __name__ == '__main__':
  main()
