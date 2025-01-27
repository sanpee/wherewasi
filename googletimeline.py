import json
from datetime import datetime, time
from typing import Literal
import pytz
from tzlocal import get_localzone
from haversine import haversine
from operator import itemgetter
from typing import NamedTuple

class Position(NamedTuple):
  lat: float
  lon: float
  
  def value(self) -> tuple:
    return (self.lat, self.lon)
  
class Box(NamedTuple):
  NorthWest: Position
  NorthEast: Position
  SouthWest: Position
  SouthEast: Position

class result:
  def __init__(self, t = time(0,0), p = (0, 0), d = 0.0, a = Literal['Path', 'End', 'Start'], id = 0) -> None:
    self.time = t
    self.position = p 
    self.distance = d
    self.activity = a
    self.timelinepathid = id # Get the actual path from googletimeline class

  def __str__(self):
    return self.activity + ':\t' + self.time.strftime('%Y-%m-%d (%a) %H:%M:%S') + ' - {0:.2f}km'.format(self.distance)  
  
class googletimeline:
  def __init__(self, json_filepath):
    f = open(json_filepath, encoding='utf8')
    timeline = json.load(f)
    self.timelineData = timeline['semanticSegments']
    self.idcounter = 0
  
  def findPathById(self, id: int) -> list: 
    path = [x for x in self.timelineData if 'timelinePath' in x.keys() and 'id' in x.keys() and x['id'] == id]
    return [] if len(path) == 0 else path[0]['timelinePath']
  
  def findLocation(self, targetLocation, distance_from_target_km, findTimeStart = None, findTimeEnd = None, findOnDateOrDay = None, include_raw_path = True ) -> list[result]:
    search_result: list[result] = []
    ###########################################################################
    # Type#1 Raw Path
    # startTime
    # endTime
    # timelinePath[ {point, time}]
    if include_raw_path:
      timelinePaths = [x for x in self.timelineData if 'timelinePath' in x.keys()]
      for t in timelinePaths:
        for pt in t['timelinePath']:
          visitLoc = googletimeline.parseLatLng(pt['point'])
          visitTime = googletimeline.parseLocalTime(pt['time'])
          distFromTarget = haversine(targetLocation, visitLoc)
          
          distOk = distFromTarget <= distance_from_target_km
          timeOk = googletimeline.isTimeInRange(findTimeStart, findTimeEnd, visitTime)
          
          if distOk and timeOk:
            # Tag the path
            if 'id' not in t.keys(): 
              self.idcounter += 1; t['id'] = self.idcounter
            found = result(visitTime, visitLoc, distFromTarget, 'Path', t['id'])
            search_result.append(found)
    
    ###########################################################################
    # Type#2 Activity e.g. Walking, Driving etc
    # startTime
    # endTime
    # activity
    # -> start { latLng }
    # -> end { latLng }
    # -> distanceMeters 
    # -> topCandidate { type, probability }
    activities = [x for x in self.timelineData if 'activity' in x.keys()]
    for a in activities:
      startTime = googletimeline.parseLocalTime(a['startTime'])
      startLoc = googletimeline.parseLatLng(a['activity']['start']['latLng'])
      distFromStart = haversine(targetLocation, startLoc)
      if distFromStart <= distance_from_target_km and googletimeline.isTimeInRange(findTimeStart, findTimeEnd, startTime):
        found = result(startTime, startLoc, distFromStart, 'Start')
        search_result.append(found)
          
      endTime = googletimeline.parseLocalTime(a['endTime'])
      endLoc = googletimeline.parseLatLng(a['activity']['end']['latLng'])
      distFromEnd = haversine(targetLocation, endLoc)
      if distFromEnd <= distance_from_target_km and googletimeline.isTimeInRange(findTimeStart, findTimeEnd, endTime):
          found = result(endTime, endLoc, distFromEnd, 'End')
          search_result.append(found)

    # Type#3 Place Visited
    # startTime
    # endTime
    # visit
    # -> probability
    # -> topCandidate
    #    -> placeId
    #    -> placeLocation -> latLng 
    
    # Not quite sure
    # startTime
    # endTime
    # timelineMemory
    # -> trip
    #    -> ...
    
    return search_result
    
  def isTimeInRange(start, end, x):
    """Return true if x is in the range [start, end]"""
    """x must be datetime object"""
    if start is None or end is None:
      return True
    x_time = time(x.hour, x.minute, x.second)
    if start <= end:
      return start <= x_time <= end
    else:
      return start <= x_time or x_time <= end

  def parseLocalTime(timetext):
    dt = datetime.fromisoformat(timetext)
    dt.replace(tzinfo=pytz.UTC)
    dt = dt.astimezone(get_localzone())
    return dt                    

  def isDayinWeek(datetext):
    return False
  
  def parseLatLng(positiontext):
    """
    Converts to latlng text to tuple (lat,lng).
    :param positiontext: Coord in "(latitude,longitude)" format.
    """
    try:
      return tuple([ float(b.strip('()')) for b in positiontext.replace('°','').split(",") ])
    except:
      return None
  
  def findBoundBox(path: list[tuple]) -> list[tuple]:
    """Find 4 corners of the bounding box"""
    maxx = max(path, key=itemgetter(0))[0]
    maxy = max(path, key=itemgetter(1))[1]
    minx = min(path, key=itemgetter(0))[0]
    miny = min(path, key=itemgetter(1))[1]
     # return ((minx, maxy), (maxx, maxy), (maxx, miny), (minx, miny))
    return ((minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy))
   
  def findBoundBox2(path: list[tuple]) -> Box:
    max_lat = max(path, key=itemgetter(0))[0]
    max_lon = max(path, key=itemgetter(1))[1]
    min_lat = min(path, key=itemgetter(0))[0]
    min_lon = min(path, key=itemgetter(1))[1]
    return Box(NorthEast=Position(max_lat, min_lon),
               NorthWest=Position(max_lat, max_lon),
               SouthEast=Position(min_lat, min_lon),
               SouthWest=Position(min_lat, max_lon)) 