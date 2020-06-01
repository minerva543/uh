from ROOT import TFile, TTree, TObject
from array import array

class TreeMaker:
  def __init__(self, filename, treename, branches, append=False, expand=False):
    self._expand = expand
    self._append = append

    if self._expand or self._append:
      self._ofile = TFile(filename, 'update')
      self._otree = self._ofile.Get(treename)
      if not self._otree:
        self._otree = TTree(treename, treename)
    else:
      self._ofile = TFile(filename, 'recreate')
      self._otree = TTree(treename, treename)
    self._branch = {}
    for branch in branches:
      self.add(branch)
    
  def __enter__(self):
    return self
  
  def __exit__(self, type, value, tb):
    self.close()

  def add(self, branch):
    try:
      name = branch['name']
      try:
        type = branch['type']
      except:
        type = 'D'

      try:
        length = branch['length']
      except:
        length = 1
    except:
      name = branch
      type = 'D'
      length = 1

    self._branch[name]  = array(type.swapcase(), [0]*length)
    if length == 1:
      self._otree.Branch(name, self._branch[name], name+'/'+type)
    else:
      self._otree.Branch(name, self._branch[name], name+'['+str(length)+']/'+type)
    
  def close(self):
    if self._expand or self._append:
      self._ofile.Write("", TObject.kOverwrite)
    else:
      self._ofile.Write()
    self._ofile.Close()
    
  def set(self, branch, value):
    try:
      branch = self._branch[branch]
    except KeyError:
      print 'No branch named', branch, 'exists'
      return
    try:
      for i in xrange(min(len(value), len(branch))):
        branch[i] = value[i]
    except TypeError:
      branch[0] = value

  def Fill(self, vars={}):
    for branch in vars:
      self.set(branch, vars[branch])
    if self._expand:
      for branch in self._branch:
        self._otree.GetBranch(branch).Fill()
    else:
      self._otree.Fill()
    
  def GetEntries(self):
    return self._otree.GetEntries()

