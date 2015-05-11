from procgame import dmd 
from procgame.dmd.sdl2_displaymanager import sdl2_DisplayManager
import sdl2
"""
"""
import os
import sys
import yaml
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
from procgame.yaml_helper import value_for_key

class AssetManager(object):
    """ The AssetManager class reads the asset_list.yaml file, loading from it Animations, Fonts, Lampshows, etc.
         the values data structure is loaded from :file:`./config/asset_list.yaml` when this submodule is loaded;
         if not found there, the asset_loader will try :file:`./asset_list.yaml` before giving up.
    """

    values = None
    game = None

    loaded_map = {}

    animations = {}
    lengths = {}
    fonts = {}
    sounds = {}
    fontstyles = {}
    numLoaded = 0
    dmd_path =""
    # screen = None
    # pygF = None
    total = ""
    
    def value_for_key_path(self, keypath, default=None):
        return value_for_key(self.values,keypath, default)

    def loadConfig(self, curr_file_path, quick_load = False):
        logger = logging.getLogger('game.assets')

        if(quick_load):
            asset_config_path = curr_file_path + "/config/asset_list_quick.yaml"
        else:
            asset_config_path = curr_file_path + "/config/asset_list.yaml"

        path = asset_config_path
        if not os.path.exists(asset_config_path): # try another location...
            logger.warning('asset configuration file found at %s' % path)

            if(quick_load):
                asset_config_path = curr_file_path + "/asset_list_quick.yaml"
            else:
                asset_config_path = curr_file_path + "/asset_list.yaml"
            path = asset_config_path

        if not os.path.exists(asset_config_path):
            logger.warning('asset configuration file found at %s' % path)

            raise ValueError, "No asset configuration file found at '" + path + "'" 

        logger.info('asset configuration found at %s' % path)
        try:
            self.values = yaml.load(open(path, 'r'))
        except yaml.scanner.ScannerError, e:
            logger.error('Error loading asset config file from %s; your configuration file has a syntax error in it!\nDetails: %s', path, e)
        except Exception, e:
            logger.error('Error loading asset config file from %s: %s', path, e)


    def __init__(self, game, quick_load = False):
        super(AssetManager, self).__init__()
        self.game = game
        self.dmd_path = game.dmd_path
        # self.screen=game.desktop.screen
        # pygame.font.init()
        # p = pygame.font.match_font('Arial')
        # if(p==None):
        #   raise ValueError, "Specific font could not be found on your system.  Please install '" + fontname + "'."
        ### josh prog par
        # self.pygF = pygame.font.Font(p,32)
        self.screen_height = sdl2_DisplayManager.inst().window_h
        self.screen_width = sdl2_DisplayManager.inst().window_w

        self.loadConfig(game.curr_file_path,quick_load)

        splash_file = self.value_for_key_path('UserInterface.splash_screen', None)
        self.rect_color = self.value_for_key_path('UserInterface.progress_bar.border', (120,120,120,255))
        self.inner_rect_color = self.value_for_key_path('UserInterface.progress_bar.fill',(255,84,84,255))
        self.bar_x = self.value_for_key_path('UserInterface.progress_bar.x_center', 0.5)
        self.bar_y = self.value_for_key_path('UserInterface.progress_bar.y_center', 0.25)

        bar_w = self.value_for_key_path('UserInterface.progress_bar.width', 0.8)
        bar_h = self.value_for_key_path('UserInterface.progress_bar.height', 0.15)

        text_y = self.value_for_key_path('UserInterface.text.y_center', 0.15)

        self.prog_bar_width = int(bar_w * self.screen_width)
        self.prog_bar_height = int(bar_h * self.screen_height)

        self.prog_bar_x = int((self.screen_width * self.bar_x) - (self.prog_bar_width/2))
        self.prog_bar_y = int((self.screen_height * self.bar_y) - (self.prog_bar_height/2))

        self.text_y = int(text_y * self.screen_height)

        if(splash_file is not None):
            s = sdl2_DisplayManager.inst().load_surface(game.dmd_path + splash_file)
            self.splash_image = sdl2_DisplayManager.inst().texture_from_surface(s)
            del s
        else:
            self.splash_image = None

        self.load()

    def updateProgressBar(self, displayType,fname):
        if(self.splash_image is not None):
            sdl2_DisplayManager.inst().screen_blit(self.splash_image, expand_to_fill=True)
        else:
            sdl2_DisplayManager.inst().clear((0,0,0,0))


        sdl2_DisplayManager.inst().draw_rect(self.rect_color, (self.prog_bar_x,self.prog_bar_y,self.prog_bar_width,self.prog_bar_height), False)
        percent = int (float(self.numLoaded + 1)/float(self.total) * self.prog_bar_width)

        sdl2_DisplayManager.inst().draw_rect(self.inner_rect_color, (self.prog_bar_x + 2,self.prog_bar_y + 2,percent,self.prog_bar_height-4), True) 

        s = "Loading %s: [%06d] of [%06d]:" % (displayType, self.numLoaded+1,self.total)
        tx = sdl2_DisplayManager.inst().font_render_text(s, font_alias=None, size=None, width=300, color=None, bg_color=None)
        sdl2_DisplayManager.inst().screen_blit(tx, x=60, y=self.text_y, expand_to_fill=False)

        tx = sdl2_DisplayManager.inst().font_render_text(fname, font_alias=None, size=None, width=300, color=None, bg_color=None)
        sdl2_DisplayManager.inst().screen_blit(tx, x=80, y=self.text_y+35, expand_to_fill=False)


    #   self.screen.blit(surf,(self.prog_bar_x,self.prog_bar_y + (1.1 * self.prog_bar_height)) )
        sdl2_DisplayManager.inst().flip()

        for event in sdl2.ext.get_events():
            #print("Key: %s" % event.key.keysym.sym)
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                    sys.exit()
   
        # pygame.display.flip()

    def clearScreen(self):
        self.screen.fill((255,0,0))
        pygame.display.flip()


    def loadIntoCache(self,key,frametime=2,file=None,repeatAnim=False,holdLastFrame=False,  opaque = False, composite_op = None, x_loc =0, y_loc=0):
        if(file==None):
            file=key + '.vga.dmd.zip'
        
        self.updateProgressBar("Animations", file)

        if(self.loaded_map.has_key(file)):
            tmp = self.animations[self.loaded_map[file]]
            #print("quick loaded '%s'" % key)
        else:
            tmp = dmd.Animation().load(self.dmd_path + file , composite_op=composite_op)
            self.loaded_map[file] = key

        self.lengths[key] = tmp.frames[-1]
        self.animations[key] = dmd.AnimatedLayer(frames=tmp.frames, frame_time=frametime, repeat=repeatAnim, hold=holdLastFrame) 
        self.animations[key].set_target_position(x_loc, y_loc)
        # if composite_op != None:
        #   self.animations[key].composite_op = composite_op
        self.numLoaded += 1

    def load(self):
        anims = self.value_for_key_path(keypath='Animations', default={})
        fonts = self.value_for_key_path(keypath='Fonts', default={})
        hfonts = value_for_key(fonts,'HDFonts',{})
        rfonts = value_for_key(fonts,'DMDFonts',{})
        fontstyles = value_for_key(fonts,'FontStyles',{})
        lamps = self.value_for_key_path(keypath='LampShows', default={})
        sounds = self.value_for_key_path(keypath='Audio', default={})
        music = value_for_key(sounds,'Music',{})
        effects = value_for_key(sounds,'Effects',{})
        voice = value_for_key(sounds,'Voice',{})
        
        # self.total = str(len(anims)+len(hfonts)+len(rfonts)+len(music)+len(effects)+len(voice))
        self.total = (len(lamps) + len(fontstyles) + len(anims)+len(hfonts)+len(rfonts)+len(music)+len(effects)+len(voice))

        try:
            current = ""            
            for l in lamps:
                k  = value_for_key(l,'key')
                fname = value_for_key(l,'file')
                self.updateProgressBar("Lampshows", fname)
                # self.lampshows = self.game.sound.register_music(k,self.game.music_path+fname, volume=volume)            
                f = self.game.lampshow_path + fname
                current = 'Lampshow: [%s]: %s, %s ' % (k, f, fname)
                self.game.lampctrl.register_show(k, f)

                # Validate the lampshow --as best as possible
                self.game.lampctrl.show.load(f, False, None)
                for tr in self.game.lampctrl.show.lampshow.tracks:
                    if tr.driver == None: # Check drivers.
                        tr.resolve_driver_with_game(self.game)
                    if tr.driver == None:
                        raise ValueError, "Name '%s' specified in lampshow does not match a driver in the machine yaml." % tr.name

                self.numLoaded += 1            
            for f in hfonts:
                k  = value_for_key(f,'key')
                sname = value_for_key(f,'systemName',k)
                size  = value_for_key(f,'size')
                self.updateProgressBar("HD Fonts", sname)
                current = 'HD font: [%s]: %s, %d ' % (k, sname, size)
                
                self.fonts[k] = dmd.hdfont_named(sname,size)
                self.numLoaded += 1

            for f in rfonts:
                k  = value_for_key(f,'key')
                fname = value_for_key(f,'file')
                self.updateProgressBar("DMD Fonts", fname)
                current = 'Font: [%s]: %s ' % (k, fname)
                self.fonts[k] = dmd.font_named(fname)
                self.numLoaded += 1

            for f in fontstyles:
                ic = value_for_key(f, 'interior_color')
                lc = value_for_key(f, 'line_color')
                lw = value_for_key(f, 'line_width')
                k = value_for_key(f, 'key')
                font_style = dmd.HDFontStyle( interior_color=ic, 
                                        line_width=lw, 
                                        line_color=lc )
                self.fontstyles[k] = font_style

        except Exception, e:
            logger.error("===ASSET MANAGER - ASSET FAILURE===")
            logger.error(current)
            logger.error("======")
            raise e

        for s in music:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            volume = value_for_key(s,'volume',.5)
            self.updateProgressBar("Audio: Music", fname)
            self.game.sound.register_music(k,self.game.music_path+fname, volume=volume)
            self.numLoaded += 1

        for s in effects:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            volume = value_for_key(s,'volume',.5)
            self.updateProgressBar("Audio SFX", fname)
            self.game.sound.register_sound(k,self.game.sfx_path+fname, volume=volume)
            self.numLoaded += 1

        for s in voice:
            k  = value_for_key(s,'key')
            fname = value_for_key(s,'file')
            channel = value_for_key(s,'channel',0)
            volume = value_for_key(s,'volume',.5)
            self.updateProgressBar("Audio Voices", fname)
            # self.game.sound.register_sound(k,self.game.voice_path+fname, channel=channel, volume=volume)
            self.game.sound.register_sound(k,self.game.voice_path+fname, volume=volume)
            self.numLoaded += 1


        for anim in anims:
            k  = value_for_key(anim,'key')
            ft = value_for_key(anim,'frame_time',2)
            f  = value_for_key(anim,'file')
            r  = value_for_key(anim,'repeatAnim',False)
            h  = value_for_key(anim,'holdLastFrame',False)
            o  = value_for_key(anim,'opaque',False)
            c  = value_for_key(anim,'composite_op')
            x  = value_for_key(anim, 'x_loc', 0)
            y  = value_for_key(anim, 'y_loc', 0)
            self.loadIntoCache(k,ft,f,r,h,o,c,x,y)

        # self.clearScreen()    


