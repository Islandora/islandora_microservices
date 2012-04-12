from islandoraUtils import DSConverter as DSC
from plugin_manager import IslandoraListenerPlugin
from islandoraUtils.metadata import fedora_relationships as RELS
import pprint
import time

class thumbnail_plugin(IslandoraListenerPlugin):
  
  def initialize(self, config_parser):
      # call the parent function (this just prints an init message to the logs
      # this is a good practice
      IslandoraListenerPlugin.initialize(self, config_parser)
      return True
  
  def fedoraMessage(self, message, obj, client):
    
    pp = pprint.PrettyPrinter(indent=4)        
    
    # obj is the originating Fedora object
    
    cmodels = message['content_models']
    method = message['method']
    changeMethods = ['addDatastream', 'purgeDatastream', 'modifyDatastreamByReference']
    
    ri = RELS.rels_int(obj)
    
    inDS = message['dsid']
    mime = obj[inDS].mimeType
    now = time.time()

    if 'islandora:genericCModel' in cmodels:
      outDS = 'JPG_' + str(now)
      DSC.create_thumbnail(obj, inDS, outDS)
      # may need a separate viewer
      ri.addRelationship(inDS,'hasThumbnail',outDS)
      if mime == 'application/pdf' and method in changeMethods: # just this
        outDS = 'SWF_' + str(now)
        DSC.create_swf(obj, inDS, outDS)
        ri.addRelationship(inDS,'hasDerivative',outDS)
    
    return True
    
  def islandoraMessage(self, method, message, client):
    pass
