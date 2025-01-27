import tkinter as Tk
import tkinter.ttk as Ttk
# Pull from 
from TkinterMapView.tkintermapview import TkinterMapView
from tkinter import messagebox
from haversine import inverse_haversine, Direction
import configparser
from googletimeline import googletimeline, Box, Position
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
      # Starts the GUI if only no error was found
      self.initUI()
      
  def initUI(self):
    self.master.title('Where was I')
    self.master.geometry(self.config['DEFAULT'].get('geometry',f'{800}x{600}'))
    self.master.protocol('WM_DELETE_WINDOW', self.onWinExit)
    self.win_size = 0
    self.master.bind("<Configure>", self.onWinResize)
    self.pack(fill=Tk.BOTH, expand=True)
    
    searchPanel = Ttk.Frame(self, height=50)
    searchPanel.pack(side=Tk.TOP, fill=Tk.BOTH)
    
    self.predefinedLocation = Tk.StringVar() 
    predefinedLocations =  Ttk.OptionMenu(searchPanel, self.predefinedLocation, *self.locations, command=self.usePredefinedLocation)
    predefinedLocations.pack(side=Tk.LEFT, padx=5, pady=5)   
    
    searchButton = Ttk.Button(searchPanel, text = 'Search', command=self.searchLocation)
    searchButton.pack(side=Tk.RIGHT, padx=5, pady=5)
    
    clearButton = Ttk.Button(searchPanel, text = 'X', width=1.1, command=lambda: self.SearchTextVar.set(''))
    clearButton.pack(side=Tk.RIGHT, padx=5, pady=5)
        
    locationEntry = Tk.Entry(searchPanel, width=1000, textvariable=self.SearchTextVar)
    locationEntry.pack(side=Tk.LEFT, padx=5, pady=5, fill=Tk.BOTH, expand=True)  
        
    self.searchResult = Ttk.Treeview(self, columns=("Date Time", "Type", "Distance(km)"), show="headings")
    self.searchResult.column(1, width=50, stretch=True)  # Type
    self.searchResult.column(2, width=100, stretch=True) # Distance(km)
    self.searchResult.bind('<ButtonRelease-1>', self.searchResultSelectItem)
    for col in self.searchResult['columns']:
      self.searchResult.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(self.searchResult, _col, False))
    
    vsb = Ttk.Scrollbar(self, orient="vertical", command=self.searchResult.yview)
    self.searchResult.configure(yscrollcommand=vsb.set)
    vsb.pack(side=Tk.RIGHT, fill=Tk.Y)
    self.searchResult.pack(side=Tk.RIGHT, fill=Tk.Y)
    
    # resultlabel = Ttk.Label(self.searchResult, width=200)
    # resultlabel = Ttk.Progressbar(self.searchResult, mode='indeterminate')
    # resultlabel.grid(row=0, column=0, sticky='news')
    self.busy = Ttk.Progressbar(self.searchResult, mode='indeterminate')
    # busy.place(x = self.searchResult.winfo_width() / 4, y=60, width=self.searchResult.winfo_width() / 2)
    #busy.place(x = 100, y=60, width=100)
    #busy.start()
            
    mapViewPanel = Ttk.Frame(self)
    mapViewPanel.pack(side=Tk.LEFT, fill=Tk.BOTH, expand=True)
    ## Invisible development mode, turn off while doing other thing
    self.mapWidget = TkinterMapView(mapViewPanel)
    tile_server_config = self.config['DEFAULT'].get('maptileurl', 'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png,19')
    self.mapWidget.set_tile_server(tile_server_config.split(',')[0], max_zoom=int(tile_server_config.split(',')[1]))
    self.mapWidget.pack(side=Tk.TOP, fill=Tk.BOTH, expand=True, padx=5, pady=5) 
    # Use a panel to hold the zoomMap just to add border
    self.zoomMapPanel = Tk.Frame(self, width=300, height=300, border=10)
    self.zoomMapWidget = TkinterMapView(self.zoomMapPanel, corner_radius=10, max_zoom=22)
    self.zoomMapWidget.set_tile_server(tile_server_config.split(',')[0], max_zoom=int(tile_server_config.split(',')[1]))
    self.zoomMapWidget.pack(fill=Tk.BOTH, expand=True)
  
  def usePredefinedLocation(self, e):
    '''
    
    '''
    q = query.QueryParser(self.SearchTextVar.get())
    q.location_name = e
    q.position = self.locationNameToPosition(e)
    self.SearchTextVar.set(q.reform())
    self.searchLocation()
  
  def searchLocation(self):
    self.searchResult.delete(*self.searchResult.get_children())
    self.mapWidget.delete_all_marker()
    self.mapWidget.delete_all_path()
    self.zoomMapWidget.delete_all_marker()        
    busy = Ttk.Progressbar(self.searchResult, mode='indeterminate')
    self.searchResult.update()
    busy.place(x = self.searchResult.winfo_width() / 4, y=60, width=self.searchResult.winfo_width() / 2)
    
    busy.start()
    searchText = self.SearchTextVar.get()
    self.config['DEFAULT']['lastsearch'] = searchText
    q = query.QueryParser(searchText)
    results = self.gtimeline.findLocation(q.position, q.distance, q.timefrom, q.timeto, q.days)
    busy.stop()
    busy.destroy()
    
    if results is not None and len(results) > 0:
      if self.mapWidget is not None:
        self.mapWidget.set_position(q.position[0], q.position[1], 
                                        marker = True, 
                                        text   = q.location_name if len(q.location_name) > 0 else q.position,
                                        range  = q.distance)
        
        self.zoomMapWidget.set_position(q.position[0], q.position[1], 
                                        marker = True, 
                                        text   = q.location_name if len(q.location_name) > 0 else q.position,
                                        range  = q.distance)
        
        # self.zoomMapWidget.fit_bounding_box( (q.position[0]-q.distance*1.1, q.position[1]-q.distance*1.1), (q.position[0]+q.distance*1.1, q.position[1]+q.distance*1.1))
        self.zoomMapWidget.fit_bounding_box(inverse_haversine(q.position, q.distance, Direction.NORTHWEST),
                                            inverse_haversine(q.position, q.distance, Direction.SOUTHEAST))
     
      for res in results:
        self.searchResult.insert('', 'end', values=(
          res.time.strftime('%Y-%m-%d (%a) %H:%M:%S'), # Column #0
          res.activity, 
          '{d:.2f}'.format(d = res.distance), 
          res.timelinepathid))
        self.zoomMapWidget.set_marker(res.position[0], res.position[1], marker_shape = 'diamond')
  
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
          #box = googletimeline.findBoundBox2(rawpath)
          #self.mapWidget.fit_bounding_box(box.NorthEast, box.SouthWest)
          #self.mapWidget.fit_bounding_box(box.NorthWest, box.SouthEast)
   
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
        self.busy.place(x = event.width / 4, y=60, width=100)
        self.busy.start()
        
  def treeview_sort_column(self, tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(reverse=reverse)
    # rearrange items in sorted positions
    for index, (val, k) in enumerate(l): tv.move(k, '', index)
    # reverse sort next time
    tv.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tv, _col, not reverse))
  
  def locationNameToPosition(self, location) -> tuple:
    position = self.config['LOCATIONS'].get(location, '(0,0)')
    return googletimeline.parseLatLng(position)
  
      
def main():
  root = Tk.Tk()
  root.minsize(1000, 600)
  WhereAmI()
  root.mainloop()  
  
if __name__ == '__main__':
  main()
