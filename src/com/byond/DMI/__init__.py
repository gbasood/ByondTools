
import sys, os, glob, string, traceback, fnmatch, math, shutil

from PIL import Image, PngImagePlugin
from .State import State
from com.byond.DMIH import *

class DMILoadFlags:
    NoImages = 1
    NoPostProcessing = 2
    

class DMI:
    version = ''
    states = {}
    iw = 32
    ih = 32
    filename = ''
    pixels = None
    size = ()
    statelist = ''
    max_x = -1
    max_y = -1
    
    def __init__(self, file):
        self.filename = file
        self.version = ''
        self.states = {}
        self.iw = 32
        self.ih = 32
        self.pixels = None
        self.size = ()
        self.statelist = 'LOLNONE'
        self.max_x = -1
        self.max_y = -1
        
    def make(self, makefile):
        print('>>> Compiling %s -> %s' % (makefile, self.filename))
        h = DMIH()
        h.parse(makefile)
        for node in h.tokens:
            if type(node) is Variable:
                if node.name == 'height':
                    self.ih = node.value
                elif node.name == 'weight':
                    self.iw = node.value
            elif type(node) is directives.State:
                self.states[node.state.name] = node.state
            elif type(node) is directives.Import:
                if node.ftype == 'dmi':
                    dmi = DMI(node.filedef)
                    dmi.extractTo("_tmp/" + os.path.basename(node.filedef))
                    for name in dmi.states:
                        self.states[name] = dmi.states[name]
                        
    def save(self, to):
            
        # Now build the manifest
        manifest = 'version = 4.0'
        manifest += '\r\n        width = {0}'.format(self.iw)
        manifest += '\r\n        height = {0}'.format(self.ih)
        
        frames = []
        # Sort by name because I'm autistic like that.
        for name in sorted(self.states):
            manifest += self.states[name].genManifest()
            frames += self.states[name].icons
            
        # Next bit borrowed from DMIDE.
        icons_per_row = math.ceil(math.sqrt(len(frames)))
        rows = icons_per_row
        if len(frames) > icons_per_row * rows:
            rows += 1
        map = Image.new('RGBA', (icons_per_row * self.iw, rows * self.ih))
        
        x = 0
        y = 0
        for frame in frames:
            # print(frame)
            icon = Image.open(frame, 'r')
            map.paste(icon, (x * self.iw, y * self.ih))
            x += 1
            if x > icons_per_row:
                y += 1
                x = 0
                    
        # More borrowed from DMIDE:
        # undocumented class
        meta = PngImagePlugin.PngInfo()

        # copy metadata into new object
        
        reserved = ('interlace', 'gamma', 'dpi', 'transparency', 'aspect')
        for k, v in map.info.items():
                if k in reserved: continue
                meta.add_text(k, v, 1)
        # Only need one - Rob
        meta.add_text(b'Description', manifest.encode('ascii'), 1)

        # and save
        map.save(to, 'PNG', pnginfo=meta)
        
        print('>>> {0} states saved to {1}'.format(len(frames), to))

    def getDMIH(self):
        o = '# DMI Header 1.0 - Generated by DMI.py'
        o += self.genDMIHLine('width', self.iw, -1)
        o += self.genDMIHLine('height', self.ih, -1)

        for s in sorted(self.states):
            o += self.states[s].genDMIH()
        
        return o
        
    def genDMIHLine(self, name, value, default):
        if value != default:
            if type(value) is list:
                value = ','.join(value)
            return '\n{0} = {1}'.format(name, value)
        return ''
    
    def extractTo(self, dest, suppress_post_process=False):
        print('>>> Extracting %s...' % self.filename)
        self.read(dest, suppress_post_process)
    
    def getFrame(self, state, dir, frame):
        if state not in self.states:
            return None
        return self.states[state].getFrame(dir, frame)
    
    def getHeader(self):
        img = Image.open(self.filename)
        # print(repr(img.info))
        if(b'Description' not in img.info):
            raise Exception("DMI Description is not in the information headers!")
        return img.info[b'Description'].decode('ascii')
    
    def setHeader(self, newHeader, dest):
        img = Image.open(self.filename)
                    
        # More borrowed from DMIDE:
        # undocumented class
        meta = PngImagePlugin.PngInfo()

        # copy metadata into new object
        
        reserved = ('interlace', 'gamma', 'dpi', 'transparency', 'aspect')
        for k, v in img.info.items():
                if k in reserved: continue
                print(k, v)
                meta.add_text(k, v, 1)
        # Only need one - Rob
        meta.add_text(b'Description', newHeader.encode('ascii'), 1)

        # and save
        img.save(dest + '.tmp', 'PNG', pnginfo=meta)
        shutil.move(dest + '.tmp', dest)
        
    def loadMetadata(self, flags=0):
        self.load(flags | DMILoadFlags.NoImages)
        
    def loadAll(self, flags=0):
        self.load(flags)
    
    def load(self, flags):
        #if self.dest is None:
        #    suppress_post_process = True
        self.img = Image.open(self.filename)
        self.size = self.img.size
        # print(repr(img.info))
        if(b'Description' not in self.img.info):
            raise Exception("DMI Description is not in the information headers!")
        self.pixels = self.img.load()
        desc = self.img.info[b'Description'].decode('ascii')
        """
version = 4.0
        width = 32
        height = 32
state = "fire"
        dirs = 4
        frames = 1
state = "fire2"
        dirs = 1
        frames = 1
state = "void"
        dirs = 4
        frames = 4
        delay = 2,2,2,2
state = "void2"
        dirs = 1
        frames = 4
        delay = 2,2,2,2
        """
        state = None
        x = 0
        y = 0
        self.statelist = desc
        ii = 0
        for line in desc.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                continue
            if '=' in line:
                (key, value) = line.split(' = ')
                key = key.strip()
                value = value.strip().replace('"', '')
                if key == 'version':
                    self.version = value
                elif key == 'width':
                    self.iw = int(value)
                    self.max_x = self.img.size[0] / self.iw
                elif key == 'height':
                    self.ih = int(value)
                    self.max_y = self.img.size[1] / self.ih
                    # print(('%s: {sz: %s,h: %d, w: %d, m_x: %d, m_y: %d}'%(self.filename,repr(img.size),self.ih,self.iw,self.max_x,self.max_y)))
                elif key == 'state':
                    if state != None:
                        # print(" + %s" % (state.ToString()))
                        if(self.iw == 0 or self.ih == 0):
                            if(len(self.states) > 0):
                                raise SystemError("Width and height for each cell are not available.")
                            else:
                                self.iw = self.img.size[0]
                                self.max_x = 1
                                self.ih = self.img.size[1]
                                self.max_y = 1
                        elif(self.max_x == -1 or self.max_y == -1):
                            self.max_x = self.img.size[0] / self.iw
                            self.max_y = self.img.size[1] / self.iw
                        for i in range(state.numIcons()):
                            icon = (x, y)
                            if (flags & DMILoadFlags.NoImages) == 0:
                                icon = self.loadIconAt(x, y)
                            state.icons += [icon]
                            x += 1
                            # print('%s[%d:%d] x=%d, max_x=%d' % (self.filename,ii,i,x,self.max_x))
                            if(x >= self.max_x):
                                x = 0
                                y += 1
                        self.states[state.name] = state
                        #if not suppress_post_process:
                        #    self.states[state.name].postProcess()
                        ii += 1
                    state = State(value)
                elif key == 'dirs':
                    state.dirs = int(value)
                elif key == 'frames':
                    state.frames = int(value)
                elif key == 'loop':
                    state.loop = int(value)
                elif key == 'rewind':
                    state.rewind = int(value)
                elif key == 'movement':
                    state.movement = int(value)
                elif key == 'delay':
                    state.delay = value.split(',')
                elif key == 'hotspot':
                    state.hotspot = value
                else:
                    print('Unknown key ' + key + ' (value=' + value + ')!')
                    sys.exit()
        
        self.states[state.name] = state
        for i in range(state.numIcons()):
            self.states[state.name].icons += [self.loadIconAt(x, y)]
            x += 1
            # print('%s[%d:%d] x=%d, max_x=%d' % (self.filename,ii,i,x,self.max_x))
            if(x >= self.max_x):
                x = 0
                y += 1
            
    def extractAllStates(self, dest, flags=0):
        for name, state in self.states.iteritems():
            state = State()
            for i in range(len(state.icons)):
                x, y = state.icons[i]
                self.extractIconAt(name, dest, x, y, i)
             
                if (flags & DMILoadFlags.NoPostProcessing) == 0:
                    self.states[state.name].postProcess()
                if dest is not None:
                    outfolder = os.path.join(dest, os.path.basename(self.filename))
                    nfn = self.filename.replace('.dmi', '.dmih')
                    valid_chars = "-_.()[] %s%s" % (string.ascii_letters, string.digits)
                    nfn = ''.join(c for c in nfn if c in valid_chars)
                    nfn = os.path.join(outfolder, nfn)
                    with open(nfn, 'w') as dmih:
                        dmih.write(self.getDMIH())
        
    def loadIconAt(self, sx, sy):
        if(self.iw == 0 or self.ih == 0):
            raise SystemError('Image is {}x{}, an invalid size.'.format(self.ih, self.iw))
        # print("  X (%d,%d)"%(sx*self.iw,sy*self.ih))
        icon = Image.new(self.img.mode, (self.iw, self.ih))
        newpix = icon.load()
        for y in range(self.ih):
            for x in range(self.iw):
                _x = x + (sx * self.iw)
                _y = y + (sy * self.ih)
                try:
                    newpix[x, y] = self.pixels[_x, _y]
                except IndexError as e:
                    print("!!! Received IndexError in %s <%d,%d> = <%d,%d> + (<%d,%d> * <%d,%d>), max=<%d,%d> halting." % (self.filename, _x, _y, x, y, sx, sy, self.iw, self.ih, self.max_x, self.max_y))
                    print('%s: {sz: %s,h: %d, w: %d, m_x: %d, m_y: %d}' % (self.filename, repr(self.img.size), self.ih, self.iw, self.max_x, self.max_y))
                    print('# of cells: %d' % len(self.states))
                    print('Image h/w: %s' % repr(self.size))
                    print('--STATES:--')
                    print(self.statelist)
                    sys.exit(1)
        return icon
                    
    def extractIconAt(self, state, dest, sx, sy, i=0):
        icon = self.loadIcon(sx, sy)
        outfolder = os.path.join(dest, os.path.basename(self.filename))
        if not os.path.isdir(outfolder):
            print('\tMKDIR ' + outfolder)
            os.makedirs(outfolder)
        nfn = state.name + "[%d].png" % i
        valid_chars = "-_.()[] %s%s" % (string.ascii_letters, string.digits)
        nfn = ''.join(c for c in nfn if c in valid_chars)
        nfn = os.path.join(outfolder, nfn)
        if os.path.isfile(nfn):
            os.remove(nfn)
        try:
            icon.save(nfn)
        except SystemError as e:
            print("Received SystemError, halting: %s" % traceback.format_exc(e))
            print('{ih=%d,iw=%d,state=%s,dest=%s,sx=%d,sy=%d,i=%d}' % (self.ih, self.iw, state.ToString(), dest, sx, sy, i))
            sys.exit(1)
        return nfn
