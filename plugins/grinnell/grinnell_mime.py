'''
Created on March 5, 2011

@author: jonathangreen
'''
from islandoraUtils.fedoraLib import get_datastream_as_file, update_datastream
from shutil import rmtree, move
from datetime import datetime
import os
import subprocess
import string
import logging

from islandoraUtils import DSConverter as DSC
from islandoraUtils.metadata.fedora_relationships import rels_int, rels_namespace, rels_object
from islandoraUtils.fedoraLib import mangle_dsid

tn_postfix = '-tn.jpg'

class GrinnellMime():
    
    def __init__(self, obj, message):
        self.obj = obj
        self.message = message
    
    def create_thumbnail(self, obj, dsid, tnid):
        r = DSC.create_thumbnail(obj, dsid, tnid)
        
        if r == 0:
            relationships = self.relsint.getRelationships(subject='TN', predicate='fromMime')
            if (not relationships and 'TN' not in obj):
                DSC.create_thumbnail(obj, dsid, 'TN')
                self.relsint.addRelationship('TN', 'fromMime', rels_object(obj[dsid].mimeType, rels_object.LITERAL))
            elif(relationships):
                current_mime = relationships[0][2].data
                new_mime = obj[dsid].mimeType
                if (current_mime.split('/')[0] != 'image') and (new_mime.split('/')[0] == 'image'):
                    DSC.create_thumbnail(obj, dsid, 'TN')
                    self.relsint.purgeRelationships(subject='TN', predicate='fromMime')
                    self.relsint.addRelationship('TN', 'fromMime', new_mime)
        return r
    
    # general call derivative function
    def call_function(self, function, dsid, did, args):
        if(args):
            r = function(self.obj, dsid, did, args)
        else:
            r = function(self.obj, dsid, did)
        
        return r
    
    # general derivative creation function
    def create_derivative(self, relationship, postfix, function, dsid=None, args=None):
        # make sure we are not creating a derivative of a derivative
        if (not self.test_derivative()):
            # we default to creating a derivative of ourselves
            if not dsid:
                dsid = self.dsid
            # see if we need a derivative
            relationships = self.relsint.getRelationships(subject=self.dsid, predicate=relationship)
            if relationships:
                did = relationships[0][2].data
                if DSC.check_dates(self.obj, self.dsid, did):
                    self.call_function(function, dsid, did, args)
                    self.relsint.update()
            else:
                did = self.dsid.rsplit('.', 1)[0]
                did += postfix
                did = mangle_dsid(did)
                if did == self.dsid or did in self.obj:
                    did = self.dsid.rsplit('.', 1)[0]
                    did += '.d'
                    did += postfix
                    did = mangle_dsid(did)
                r = self.call_function(function, dsid, did, args)
                if( r == 0 ):
                    self.relsint.addRelationship(self.dsid, relationship, did)
                    self.relsint.update()
    
    # test derivative - returns true if the dsid is a derivative.
    def test_derivative(self):
        relationships = self.relsint.getRelationships(object=self.dsid)
        if(relationships):
            return True
        else:
            return False
    
    # meta functions called by multiple mime functions
    def video_derivative(self):
        self.create_derivative('hasMP4', '.mp4', DSC.create_mp4)
        relationship = self.relsint.getRelationships(subject=self.dsid, predicate='hasMP4')
        if(relationship):
            mp4id = relationship[0][2].data
            self.create_derivative('hasThumbnail', tn_postfix, self.create_thumbnail, mp4id)
    
    def image_derivative(self):
        self.create_derivative('hasThumbnail', tn_postfix, self.create_thumbnail)
        # self.create_derivative('hasJP2', '.jp2', DSC.create_jp2)
    
    def document_derivative(self):
        self.create_derivative('hasPDF', '.pdf', DSC.create_pdf)
        # get name of pdf to create swf and thumbnail from
        relationship = self.relsint.getRelationships(subject=self.dsid, predicate='hasPDF')
        if(relationship):
            pdfid = relationship[0][2].data
            self.create_derivative('hasThumbnail', tn_postfix, self.create_thumbnail, pdfid)
            self.create_derivative('hasSWF', '.swf', DSC.create_swf, pdfid)
    
    def audio_derivative(self):
        args = ['-mm', '--cbr', '-b96']
        self.create_derivative('hasMP3', '.mp3', DSC.create_mp3, args=args)
        self.create_derivative('hasOGG', '.ogg', DSC.create_ogg)
    
    ##
    ## functions need to be defined for each mimetype to be worked on
    ##
    
    # video stuff
    def video_mp4(self):
        self.video_derivative()
    def video_quicktime(self):
        self.video_derivative()
    def video_x_ms_wmv(self):
        self.video_derivative()
    
    # document stuff
    def application_pdf(self):
        self.create_derivative('hasThumbnail', tn_postfix, self.create_thumbnail)
        self.create_derivative('hasSWF', '%.swf', DSC.create_swf) # create multiple SWFs per page
    def application_vnd_ms_powerpoint(self):
        self.document_derivative()
    def application_vnd_ms_excel(self):
        self.document_derivative()
    def application_msword(self):
        self.document_derivative()
    def application_vnd_openxmlformats_officedocument_spreadsheetml_sheet(self):
        self.document_derivative()
    def application_vnd_openxmlformats_officedocument_presentationml_presentation(self):
        self.document_derivative()
    def application_vnd_openxmlformats_officedocument_wordprocessingml_document(self):
        self.document_derivative()
    def text_rtf(self):
        self.document_derivative()
    
    # image stuff
    def image_jpeg(self):
        self.image_derivative()
        self.create_derivative('hasSWF', '.swf', self.jpeg_to_swf)
    def image_png(self):
        self.image_derivative()
        self.create_derivative('hasSWF', '.swf', self.png_to_swf)
    def image_tif(self):
        self.image_derivative()
    def image_tiff(self):
        self.image_derivative()
    def image_jp2(self):
        self.image_derivative()
    def image_gif(self):
        self.create_derivative('hasThumbnail', tn_postfix, self.create_thumbnail)
    
    # audio stuff
    def audio_x_wav(self):
        self.audio_derivative()
    def audio_mpeg(self):
        self.audio_derivative()
    
    # mimetype isn't found, do nothing
    def mimetype_none(self):
        pass
    
    # this is a simple dispatcher that will run functions based on mimetype
    def dispatch(self, dsid):
        self.relsint = rels_int(self.obj, rels_namespace('grinnell', 'http://www.grinnell.edu/ontologies/relsint'), 'grinnell')
        self.dsid = dsid
        try:
            # translate - / + . into _ for the mimetype function
            trantab = string.maketrans('-/+.','____')
            mime =  self.obj[dsid].mimeType.encode('ascii')
            mime_function_name = mime.translate(trantab)
            # get the function from the self object and run it
            mime_function = getattr( self, mime_function_name, self.mimetype_none )
            mime_function()
        except KeyError:
            # we catch a key error because .mimeType throws one
            # if no mimeType is defined
            pass
    
    def jpeg_to_swf(self,obj,dsid,swfid):
      self.image_to_swf(obj,dsid,swfid,'jpeg')
    
    def png_to_swf(self,obj,dsid,swfid):
      self.image_to_swf(obj,dsid,swfid,'png')
    
    def image_to_swf(self,obj,dsid,swfid,source):
      logger = logging.getLogger('islandoraUtils.DSConverter.create_swf')
      #recieve PDF create a SWF for use with flexpaper
      directory, file = get_datastream_as_file(obj, dsid, source)
      
      converter = subprocess.Popen([source+'2swf', directory+'/'+file, '-o', directory+'/'+swfid,\
           '-T 9'], stdout=subprocess.PIPE)
      out, err = converter.communicate()
      if converter.returncode != 0:
          # logger.warning('PID:%s DSID:%s SWF creation failed. Trying alternative.' % (obj.pid, dsid))
          # converter = subprocess.Popen(['pdf2swf', directory+'/'+file, '-o', directory+'/'+swfid,\
           #    '-T 9', '-f', '-t', '-s', 'storeallcharacters', '-G', '-s', 'poly2bitmap'], stdout=subprocess.PIPE)
          # out, err = converter.communicate()
          pass
      
      # catch the case where PDF2SWF fails to create the file, but returns
      if converter.returncode == 0 and os.path.isfile(directory + '/' + swfid):
          update_datastream(obj, swfid, directory+'/'+swfid, label=source+' to swf', mimeType='application/x-shockwave-flash')
          r = 0
      elif not os.path.isfile(directory + '/' + swfid):
          logger.warning('PID:%s DSID:%s SWF creation failed (converter returned: "%s").' % (obj.pid, dsid, out))
          r = 1
      else:
          logger.warning('PID:%s DSID:%s SWF creation failed (converter return code:%d).' % (obj.pid, dsid, pdf2swf.returncode))
          r = converter.returncode
      
      rmtree(directory, ignore_errors=True)
      return r
      
      