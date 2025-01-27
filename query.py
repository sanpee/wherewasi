from datetime import time
import ply.lex as lex

class QueryParser:
  '''
  Location query:
  @Name: Named location as stored in wherewasi.ini
  (lattitude, longitude)
  from H1:M1 to H2:M2 - to is optional but time format must be in 24H
  whithin Xkm 
  on weekday/weekend/mon,tue etc. Not working yet
  '''
    
  def __init__(self, text):
    self.location = (0,0)
    self.timefrom: time = None
    self.timeto: time = None
    self.distance = 0.5
    self.location_name = ''
    self.days = ''
    
    tokens = (
      'LOCATION',
      'TIMEFROM',
      'TIMETO',
      'DISTANCE',
      'LOCATION_NAME',
      'ON'
    )
    
    def t_DISTANCE(t):
      r'within\s+([0-9]*[.])?[0-9]+km'
      t.value = float(t.value.lower().replace('km','').replace('within','').strip())    
      return t

    def t_TIMEFROM(t):
      r'from\s+([0-9]*[:])?[0-9]+'
      timetext = t.value.lower().replace('from','').strip()
      timetext = timetext.split(':')
      t.value = time(int(timetext[0]), int(timetext[1]))    
      return t
  
    def t_TIMETO(t):
      r'to\s+([0-9]*[:])?[0-9]+'
      timetext = t.value.lower().replace('to','').strip()
      timetext = timetext.split(':')
      t.value = time(int(timetext[0]), int(timetext[1]))    
      return t

    def t_LOCATION(t):
      r'\(\s*[+-]?([0-9]*[.])?[0-9]+\s*\,\s*[+-]?([0-9]*[.])?[0-9]+\s*\)'
      t1 = t.value.strip('()').split(',')
      t.value = (float(t1[0]), float(t1[1]))
      return t

    def t_LOCATION_NAME(t):
      r'@\w+'
      t.value = t.value.strip('@')
      return t

    def t_ON(t):
      r'on\s(.*)'
      t.value = t.value.replace('on', '').strip()
      return t

    def t_error(t):
      t.lexer.skip(1)
      
    lexer = lex.lex()
    lexer.input(text.strip().lower())
    
    for tok in lexer:
      match tok.type: 
        case 'LOCATION': self.position = tok.value
        case 'LOCATION_NAME': self.location_name = tok.value
        case 'TIMEFROM': self.timefrom = tok.value
        case 'TIMETO': self.timeto = tok.value
        case 'DISTANCE': self.distance = tok.value
        case 'ON': self.days = tok.value
  
  def __str__(self):
    timeText = ''
    if (self.timefrom is not None and self.timefrom is not None):
      timeText = 'from {0} to {1}'.format(
        self.timefrom.strftime("%H:%M"), 
        self.timeto.strftime("%H:%M"))

    return '{0}{1}{2} within {3}km on {4}'.format(
      '@' + self.location_name if len(self.location_name) > 0 else '',
      self.position, 
      ',' + timeText if len(timeText) > 0 else '',
      self.distance, 
      self.days) 

  def reform(self) -> str:
    return self


if __name__ == '__main__':
  test = '(12.3,45.6) to 17:00 from 15:12 within 0.5km'
  test = '(12.3,45.6) to 17:00 from 15:12'
  # test = '(Hello_World) to 17:00 from 15:12'
  test = '(1.3155484,103.8976849) within 0.4km'
  test = '(1.4182134,103.8385464) from 17:00 to 19:00 within 0.2km'
  test = '@hello_world (1.3155484,103.8976849) within 0.3km on weekdays'
  test = '@hello_world (1.3155484,103.8976849) within 0.3km on 2024-12-01'
  # test = '(1.3155484,103.8976849) within 0.4km'
  q = QueryParser(test)
  print(q.reform())
    