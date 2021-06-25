from ROOT import TChain, TMath
from time import time
from array import array

class TreeWrapper:
  def __init__(self, file, name):
    self.shouldPrint = False
    self._branchOnAccess = False
    self._tree = TChain(name)
    self._functions = {}
    if isinstance(file, str):
      self.addFile(file)
    else:
      for f in file:
        self.addFile(f)
    self._cache = {}
    self._aliases = {}

  def addFile(self, file):
    self._tree.Add(file)
    
  def addFriend(self, friend):
    self._tree.AddFriend(friend)

  def removeFriend(self, friend):
    self._tree.RemoveFriend(friend)
    
  def getEntry(self):
    return self._currentEntry

  def entry(self, quiet = False, printfreq=1000, Nentries=None, branchonaccess=True, timeremaining=True, offset=0):
    self._branchOnAccess = branchonaccess
#    if branchonaccess:
#      self._tree.SetBranchStatus('*', 0)
#    else:
#      self._tree.SetBranchStatus('*', 1)
    if printfreq <= 0:
      printfreq = 1

    if Nentries == None or Nentries < 0 or Nentries > self._tree.GetEntries():
      Nentries = self._tree.GetEntries()
    if timeremaining:
      starttime = time()
    for i in range(offset, Nentries):
#      self._currentEntry = i
      if not self._branchOnAccess:
        self._tree.GetEntry(i)
      else:
        self._currentEntry = self._tree.LoadTree(i)


      if not quiet and i%int(printfreq) == 0:
        self.shouldPrint = True
        displaystr = 'Processing entry: ' + str(i) + ' ({:.2f}%)'.format(i*100./Nentries)
        if timeremaining and i > 0:
          tr = (time() - starttime)/i*(Nentries - i)
          timestr = ''
          if tr > 86400:
            days = int(tr/86400)
            timestr += ' ' + str(days) + ' days'
            tr -= days*86400
          if tr > 3600:
            hours = int(tr/3600)
            timestr += ' ' + str(hours) + ' hours'
            tr -= hours*3600
          if tr > 60:
            mins = int(tr/60)
            timestr += ' ' + str(mins) + ' min'
            tr -= mins*60
          timestr += ' ' + str(int(tr)) + ' s'
            
          displaystr += ' Remaining: ' + timestr
        print(displaystr)
      else:
        self.shouldPrint = False
      yield i
    if not quiet:
      try:
        print('Processed ', i+1, 'entries')
      except:
        print('No entries processed')

  def getFileStartLength(self, filename):
    for whichtree, chainfile in enumerate(self._tree.GetListOfFiles()):
      if chainfile.GetTitle() == filename:
        self._tree.GetEntries()
        start = self._tree.GetTreeOffset()[whichtree]
        try:
          length = chainfile.GetEntries() #self._tree.GetTreeOffset()[whichtree+1] - start
        except:
          length = None
        return (start, length)
    return None

  def GetEntries(self, selection=None):
    if not selection:
      return self._tree.GetEntries()
    return self._tree.GetEntries(selection)

  def GetMinimum(self, name):
    try:
      name = self._aliases[name]
    except:
      pass
    return self._tree.GetMinimum(name)

  def GetMaximum(self, name):
    try:
      name = self._aliases[name]
    except:
      pass
    return self._tree.GetMaximum(name)

  def tree(self):
    return self._tree

  def addAlias(self, new, old):
    self._aliases[new] = old

  def __getattr__(self, name):
#    if name == 'Entry$':
#      return self._currentEntry

    try:
      name = self._aliases[name]
    except:
      pass

    if not self._branchOnAccess:
      return getattr(self._tree, name)
    try:
      branch = self._tree.GetBranch(name)
      if not name in self._cache:
        title = branch.GetTitle().split('/')
        type = title[1].swapcase().replace('o', 'b').replace('s', 'h').replace('S', 'H')
        try:
          lengthvar = title[0].split('[')[1][:-1]
        except:
          lengthvar = None
#        print('Adding ', name, type, length)
        self._cache[name] = [None, -1, lengthvar, type]

      cache = self._cache[name]
      length = 0
      if cache[2]:
        length = getattr(self, cache[2])

      if cache[1] != self._currentEntry:
        if not cache[0] or (cache[2] and len(cache[0]) < length):
          address = array(cache[3], (2*length+1)*[0])
          cache[0] = address
          self._tree.SetBranchAddress(name, address)
        branch.GetEntry(self._currentEntry)
        cache[1] = self._currentEntry

      if cache[2]:
        return cache[0][0:length]
      return cache[0][0]
    except:
      raise AttributeError("%r object has no attribute %r" % (self.__class__, name))

  def get(self, what):
    try:
      return getattr(self, what)
    except:
      try:
        return self._functions[what](self)
      except:
        func = ''
        word = ''
        for l in what:
          if l in ' +-*/^()[]<>=&|!,':
            if self.has(word):
              func += 't.'
            func += word+l
            word = '';
          else:
            word += l

        if word:
          if self.has(word):
            func += 't.'
          func += word
        func = func.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').replace('^', '**').replace('::', '.').replace('Entry$', 't.getEntry()')
        self._functions[what] = eval('lambda t: '+func)
        return self._functions[what](self)

  def has(self, what):
    try:
      what = self._aliases[what]
    except:
      pass
    return (self._tree.GetBranch(what) != None)
    
  def searchBranch(self, what):
    retlist = []
    for branch in self._tree.GetListOfBranches():
      if what in branch.GetName():
        retlist.append(branch.GetName())
    return retlist

  def listBranches(self):
    retlist = []
    for branch in self._tree.GetListOfBranches():
      retlist.append(branch.GetName())
    return retlist

  def DrawWith(self, hist, func, select='', option=''):
    if not hist.GetName():
      hist.SetName('mmtmp_draw')
    self._tree.Draw(func+'>>'+hist.GetName(), select, option)
    if hist.GetName() == 'mmtmp_draw':
      hist.SetName('')

  def Draw(self, func, select='', option=''):
    return self._tree.Draw(func, select, option)

  def __str__(self):
    return 'TreeWrapper for ' + str(self._tree)

  def __repr__(self):
    return 'TreeWrapper for ' + str(self._tree)
