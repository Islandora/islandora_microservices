from islandoraUtils import DSConverter as DSC
from plugin_manager import IslandoraListenerPlugin
from islandoraUtils.metadata.fedora_relationships import rels_namespace, rels_object, rels_int
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
    
    relsint = rels_int(obj)
    
    inDS = message['dsid']
    mime = obj[inDS].mimeType
    now = time.time()

    if 'islandora:genericCModel' in cmodels:
      # outDS = 'JPG_' + str(now)
      # DSC.create_thumbnail(obj, inDS, outDS) # leads to an infinite loop .. don't need that!
      # may need a separate viewer
      # ri.addRelationship(inDS,'hasThumbnail',outDS)
      if mime == 'application/pdf' and method in changeMethods: # just this
        outDS = 'SWF_' + str(now)
        DSC.create_swf(obj, inDS, outDS)
        relsint.addRelationship(inDS,'hasDerivative',outDS)
        relsint.update()
    return True
    
  def islandoraMessage(self, method, message, client):
    pass
