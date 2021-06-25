###############################################################################
#                                                                             #
#                  A tutorial for multivariate selections                     #
#                                                                             #
###############################################################################

# A multivariate selection (MVA) is a machine learning tool to classify events
# as signal or background. It looks at the distributions of samples of signal
# and background, and is trained to find the differences. This script will
# train a simple classifier using ROOT's TMVA package.


from ROOT import TFile, TMVA, TCanvas

#Make an output file for the diagnostic information/plots
outfile = TFile('diagnostic.root', 'recreate')

#this does the bulk of the work
factory = TMVA.Factory('classifier', outfile, '!V:!Silent:Color:DrawProgressBar')

#Make a class to manage the data and add the variables we want to use
dataloader = TMVA.DataLoader('classifier_trainingset')
dataloader.AddVariable('B_PT',             'B_PT',             '', 'F')
dataloader.AddVariable('B_ENDVERTEX_CHI2', 'B_ENDVERTEX_CHI2', '', 'F')
dataloader.AddVariable('B_IPCHI2_OWNPV',   'B_IPCHI2_OWNPV',   '', 'F')
dataloader.AddVariable('B_FDCHI2_OWNPV',   'B_FDCHI2_OWNPV',   '', 'F')
dataloader.AddVariable('B_DIRA_OWNPV',     'B_DIRA_OWNPV',     '', 'F')
dataloader.AddVariable('K_PT',             'K_PT',             '', 'F')
dataloader.AddVariable('pi_PT',            'pi_PT',            '', 'F')
dataloader.AddVariable('muplus_PT',        'muplus_PT',        '', 'F')
dataloader.AddVariable('muminus_PT',       'muminus_PT',       '', 'F')


#Add a signal and background sample
sigfile = TFile('data/B2JPsiKst_MC.root') # MC as a signal proxy
bkgfile = TFile('data/B2JPsiKst_sideband.root') # upper mass sideband as background proxy

sigtree = sigfile.Get('DecayTree')
bkgtree = bkgfile.Get('DecayTree')

dataloader.AddSignalTree(sigtree)
dataloader.AddBackgroundTree(bkgtree)


#add the BDT method with an AdaBoost algorithm
bdtmethod = factory.BookMethod(dataloader, TMVA.Types.kBDT, 'BDT', "!H:!V:NTrees=850:MinNodeSize=2.5%:MaxDepth=3:BoostType=AdaBoost:AdaBoostBeta=0.5:UseBaggedBoost:BaggedSampleFraction=0.5:SeparationType=GiniIndex:nCuts=20")

#Do the training
factory.TrainAllMethods()
factory.TestAllMethods()
factory.EvaluateAllMethods()

outfile.Close()

###############################################################################
#                                                                             #
#                        Open the diagnostics file                            #
#                                                                             #
###############################################################################

TMVA.TMVAGui('diagnostic.root')


###############################################################################
#                                                                             #
#                  Apply the trained BDT to a data sample                     #
#                                                                             #
###############################################################################

#creat the reader for the BDT weights
reader = TMVA.Reader('!Color:Silent')

#Add the variables to the reader
from array import array
B_PT             = array('f', [0.])
B_ENDVERTEX_CHI2 = array('f', [0.])
B_IPCHI2_OWNPV   = array('f', [0.])
B_FDCHI2_OWNPV   = array('f', [0.])
B_DIRA_OWNPV     = array('f', [0.])
K_PT             = array('f', [0.])
pi_PT            = array('f', [0.])
muplus_PT        = array('f', [0.])
muminus_PT       = array('f', [0.])
reader.AddVariable("B_PT",             B_PT)
reader.AddVariable("B_ENDVERTEX_CHI2", B_ENDVERTEX_CHI2)
reader.AddVariable("B_IPCHI2_OWNPV",   B_IPCHI2_OWNPV)
reader.AddVariable("B_FDCHI2_OWNPV",   B_FDCHI2_OWNPV)
reader.AddVariable("B_DIRA_OWNPV",     B_DIRA_OWNPV)
reader.AddVariable("K_PT",             K_PT)
reader.AddVariable("pi_PT",            pi_PT)
reader.AddVariable("muplus_PT",        muplus_PT)
reader.AddVariable("muminus_PT",       muminus_PT)

#Tell the reader where to find the weights
reader.BookMVA('classifier', 'classifier_trainingset/weights/classifier_BDT.weights.xml')

#now we can apply the BDT to the data

from TreeMaker import TreeMaker
from TreeWrapper import TreeWrapper

with TreeMaker("B2JPsiKst_data_withBDT.root", "DecayTree", ["B_M", "B_PT", "B_ENDVERTEX_CHI2", "B_IPCHI2_OWNPV", "B_FDCHI2_OWNPV", "B_DIRA_OWNPV", "Kst_M", "JPsi_M", "K_PT", "pi_PT", "muplus_PT", "muminus_PT", "BDT"]) as outtree:
  tree = TreeWrapper("data/B2JPsiKst_data.root", "DecayTree")
  for entry in tree.entry():
    #give the reader the data it needs
    B_PT[0]             = tree.B_PT
    B_ENDVERTEX_CHI2[0] = tree.B_ENDVERTEX_CHI2
    B_IPCHI2_OWNPV[0]   = tree.B_IPCHI2_OWNPV
    B_FDCHI2_OWNPV[0]   = tree.B_FDCHI2_OWNPV
    B_DIRA_OWNPV[0]     = tree.B_DIRA_OWNPV
    K_PT[0]             = tree.K_PT
    pi_PT[0]            = tree.pi_PT
    muplus_PT[0]        = tree.muplus_PT
    muminus_PT[0]       = tree.muminus_PT


    outtree.Fill({
                   "B_M":tree.B_M,
                   "B_PT":tree.B_PT,
                   "B_ENDVERTEX_CHI2":tree.B_ENDVERTEX_CHI2,
                   "B_IPCHI2_OWNPV":tree.B_IPCHI2_OWNPV,
                   "B_FDCHI2_OWNPV":tree.B_FDCHI2_OWNPV,
                   "B_DIRA_OWNPV":tree.B_DIRA_OWNPV,
                   "Kst_M":tree.Kst_M,
                   "JPsi_M":tree.JPsi_M,
                   "K_PT":tree.K_PT,
                   "pi_PT":tree.pi_PT,
                   "muplus_PT":tree.muplus_PT,
                   "muminus_PT":tree.muminus_PT,
                   "BDT":reader.EvaluateMVA('classifier') #the output of the classifier
                 })

canvas = TCanvas()
tree = TreeWrapper("B2JPsiKst_data_withBDT.root", "DecayTree")
tree.Draw("B_M", "BDT > -1",  "") # no BDT cut
tree.Draw("B_M", "BDT >  0",  "same") # A loose BDT cut
tree.Draw("B_M", "BDT > 0.2", "same") # A tight BDT cut
canvas.Modified()
canvas.Update()
input("Press ENTER to exit")
