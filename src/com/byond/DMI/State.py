from com.byond import directions
from PIL import Image
import logging

class State:    
    def __init__(self, nm):
        self.name = nm
        self.hotspot = ''
        self.frames = 0
        self.dirs = 1
        self.movement = 0
        self.loop = 0
        self.rewind = 0
        self.delay = []
        self.icons = []
        self.positions = []
        
    def genManifest(self):
        '''
state = "void"
        dirs = 4
        frames = 4
        delay = 2,2,2,2
        '''
        o = '\r\nstate = "{0}"'.format(self.name)
        o += self.genManifestLine('hotspot', self.hotspot, '')
        o += self.genManifestLine('frames', self.frames, -1)
        o += self.genManifestLine('dirs', self.dirs, -1)
        o += self.genManifestLine('movement', self.movement, 0)
        o += self.genManifestLine('loop', self.loop, 0)
        o += self.genManifestLine('rewind', self.rewind, 0)
        o += self.genManifestLine('delay', self.delay, [])
        
        return o
    
    def genDMIH(self):
        o = '\r\nstate "%s" {' % self.name
        o += self.genDMIHLine('hotspot', self.hotspot, '')
        o += self.genDMIHLine('frames', self.frames, -1)
        tdirs = 'ONE'
        if self.dirs == 4:
            tdirs = 'CARDINAL'
        elif self.dirs == 8:
            tdirs = 'ALL'
        o += self.genDMIHLine('dirs', tdirs, '')
        o += self.genDMIHLine('movement', self.movement, 0)
        o += self.genDMIHLine('loop', self.loop, 0)
        o += self.genDMIHLine('rewind', self.rewind, 0)
        o += self.genDMIHLine('delay', self.delay, [])
        
        o += '\n\timport pngs {' 
        for vdir in range(self.dirs):
            _dir = directions.IMAGE_INDICES[vdir]
            o += '\n\t\tdirection "%s" {' % directions.getNameFromDir(_dir)
            for f in range(self.frames):
                o += '\n\t\t\t"%s"' % self.getFrame(_dir, f)
            o += '\n\t\t}'
        o += '\n\t}'
        o += "\n}"
        return o
        
    def genDMIHLine(self, name, value, default):
        if value != default:
            if type(value) is list:
                value = ','.join(value)
            return '\n\t{0} = {1}'.format(name, value)
        return ''
        
    def genManifestLine(self, name, value, default):
        if value != default:
            if type(value) is list:
                value = ','.join(value)
            return '\n\t{0} = {1}'.format(name, value)
        return ''
    
    def ToString(self):
        o = '%s: %d frames, ' % (self.name, self.frames)
        o += '%d directions' % self.dirs
        # o += ' icons: ' + repr(self.icons)
        return o
    
    def numIcons(self):
        return self.frames * self.dirs
    
    def getFrameIndex(self,direction,frame):
        _dir = 0
        if self.dirs == 4 or self.dirs == 8:
            _dir = directions.IMAGE_INDICES.index(direction)
            if self.dirs == 4 and _dir > 3:
                _dir = 0
        
        frame = _dir + (frame * self.dirs)
        if frame > len(self.icons):
            logging.warn('Only {} icons in state, args {{dir:{}, frame:{}}}: {}'.format(len(self.icons), direction, frame, self.ToString()))
        return frame
    
    def getFrame(self, direction, frame):
        return self.icons[self.getFrameIndex(direction, frame)]
    
    def setFrame(self, direction, frame,img):
        fi = self.getFrameIndex(direction, frame)
        if len(self.icons) < fi:
            shouldBeSize=1
            if fi > 7:
                logging.error('Unable to set frame: State uninitialized with that many frames.')
                return
            elif fi > 3:
                shouldBeSize=8
            elif fi > 0:
                shouldBeSize=4
            while len(self.icons) < shouldBeSize:
                self.icons.append(Image.new('RGBA',(32,32)))
            logging.warn('{0} now has {1} frames.'.format(self.name,len(self.icons)))
        self.icons[fi]=img
    
    def postProcess(self):
        # So old I forgot what everything did.
        return
