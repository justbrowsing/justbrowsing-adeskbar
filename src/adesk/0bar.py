# -*- coding: utf-8 -*-

# python modules
import os
import sys

# extra modules
import gtk
import cairo
import gobject
import traceback

try:
    import keybinder
    KEYBINDER_PRESENT = True
except:
    KEYBINDER_PRESENT = False    

# adeskbar modules
import ui
import barconf
import config
import desktop
import core
import draw
#~ import rundialog
#~ import terminal

#~ from draw import *

ID_CMD, ID_ICON, ID_NAME  = 0, 1, 2

## Only for debugging : False / True
DEBUG = 0

## Icon theme
ICON_THEME = gtk.icon_theme_get_default()

class BarManager():
    """ class App - main bar config/function """
    
    def __init__(self, cfg_file):
        self.cfg_file = cfg_file
        
        ## Init some var.
        self.plg_mgr = None
        self.tooltip = None
        self.bar_conf = None
        self.win = None

        self.init_flag = False
        self.bar_hidden = False
        self.mouse_over = False
        self.can_hide = True
        
        self.last_event_time = None

        if desktop.HAS_WNCK:
            self.wnck = desktop.Wnck(self)
        else:
            self.wnck = None

        ## Load user/default config
        self.load_config()
        self.create_menu()

        self.init_bar_callback()

        #~ self.rundialog = rundialog.RunDialog(self)
        #~ self.terminal = terminal.Terminal(self)
        
        ## global keybind
        #~ gobject.timeout_add(2000, self.set_keybind)

    def set_keybind(self):
        keystr = "<Super>r"
        ret = keybinder.bind(keystr, self.keybinder_callback, self.rundialog)
        print 'retour keybind :', ret
        
        #~ keystr = "<Super>space"
        #~ keybinder.bind(keystr, self.keybinder_callback, self.terminal)
        
    def keybinder_callback(self, user_data):
        user_data.toggle()

    def create_bar(self):
        """ create and configure gtk.Window (bar) """
        core.logINFO('create_bar', 'bar')
        self.win = ui.Window()
        self.win.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
        self.win.set_title("ADeskBar")
        self.win.set_name("ADeskBar")
        self.is_composited = self.win.is_composited()
        self.set_geometry()

    def set_geometry(self):
        if self.cfg['fixed_mode']:
            screen_width, screen_height = gtk.gdk.screen_width(), gtk.gdk.screen_height()
            padding = max(self.cfg['padding'], self.cfg['icon_size'] * self.cfg['zoom_factor'] - self.cfg['icon_size'])
            min_size = int(padding + self.cfg['padding'] + self.cfg['icon_size'])

            if self.cfg['position'] == "bottom" or self.cfg['position'] == "top":
                req_size = int(screen_width * self.cfg['fixed_size']/100.0)
                self.win.set_geometry_hints(None, min_width=req_size, min_height=min_size, max_width=req_size, max_height=min_size, base_width=-1, base_height=-1, width_inc=-1, height_inc=-1, min_aspect=-1.0, max_aspect=-1.0)
            else:
                req_size = int(screen_height * self.cfg['fixed_size']/100.0)
                self.win.set_geometry_hints(None, min_width=min_size, min_height=req_size, max_width=min_size, max_height=req_size, base_width=-1, base_height=-1, width_inc=-1, height_inc=-1, min_aspect=-1.0, max_aspect=-1.0)
        else:
            self.win.set_geometry_hints(None, min_width=-1, min_height=-1, max_width=-1, max_height=-1, base_width=-1, base_height=-1, width_inc=-1, height_inc=-1, min_aspect=-1.0, max_aspect=-1.0)

    def init_bar_callback(self):
        ## Window callback
        self.win.connect("button_press_event", self.bar_released)
        self.win.connect("leave-notify-event", self.bar_leave_notify)
        self.win.connect("enter-notify-event", self.bar_enter_notify)
        self.win.connect('expose-event', self.expose)
        self.win.connect('screen-changed', self.reposition)
        self.win.connect('size-allocate', self.win_size_allocate)
        self.win.connect("realize", self.update_strut)
        self.win.connect("composited-changed", self.composite_changed)

    def composite_changed(self, widget):
        self.is_composited = self.win.is_composited()
        self.update_all()
        
    def update_strut(self, widget):
        """  """
        # window need to be realize before change strut
        if widget.window == None:
            return        
        
        # reset struct
        widget.window.property_change("_NET_WM_STRUT", "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, [0,0,0,0])
        
        # only set strut if "panel" mode
        if not (self.cfg['fixed_mode'] and  self.cfg['reserve_space']):
            return

        x, y, w, h = widget.get_allocation()

        if self.cfg['position'] == "bottom" or self.cfg['position'] == "top":
            h = self.cfg['icon_size'] + 2*self.cfg['padding']
        else:
            w = self.cfg['icon_size'] + 2*self.cfg['padding']

        if self.cfg['auto_hide'] and self.bar_hidden:
            if self.cfg['position'] == "bottom" or self.cfg['position'] == "top":
                h = self.cfg['hidden_size']
            else:
                w = self.cfg['hidden_size']
                
        if self.cfg['position'] == "bottom":
            if not self.bar_hidden and not self.cfg['bar_style'] == 0: h += self.cfg['offset_pos'] 
            widget.window.property_change("_NET_WM_STRUT", "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, [0,0,0,h])

        elif self.cfg['position'] == "top":
            if not self.bar_hidden and not self.cfg['bar_style'] == 0: h += self.cfg['offset_pos'] 
            widget.window.property_change("_NET_WM_STRUT", "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, [0,0,h,0])

        elif self.cfg['position'] == "left":
            if not self.bar_hidden and not self.cfg['bar_style'] == 0: w += self.cfg['offset_pos'] 
            widget.window.property_change("_NET_WM_STRUT", "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, [w,0,0,0])

        elif self.cfg['position'] == "right":
            if not self.bar_hidden and not self.cfg['bar_style'] == 0: w += self.cfg['offset_pos'] 
            widget.window.property_change("_NET_WM_STRUT", "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, [0,w,0,0])

    def win_size_allocate(self, widget, allocation):
        self.init_bar_pos()
        self.bar_move()

    def restart(self, widget=None):
        self.win.hide()
        for index in self.plg_mgr.plugins:
            self.plg_mgr.plugins[index].destroy()
        self.win.destroy()
        self.load_config()

    def create_menu(self):
        ## Edit preferences
        self.popupMenu = gtk.Menu()
        menuPopup = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        menuPopup.connect("activate", self.edit_config)
        self.popupMenu.add(menuPopup)
        
        ## Quit (really ?)
        menuPopup = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        menuPopup.connect("activate", self.doquit)
        self.popupMenu.add(menuPopup)
     
        self.popupMenu.show_all()

    def resize_and_seticon(self, data=None):
        # resize and update icon for all plugins
        for ind in self.plg_mgr.plugins:
            self.plg_mgr.plugins[ind].resize()
            self.plg_mgr.plugins[ind].set_icon()
            self.plg_mgr.plugins[ind].restart()
        self.update_all()
        
        ## call from timer .. 
        return False

    def load_config(self):
        self.cfg, self.launcher, self.drawer = config.read(self.cfg_file)

        ## If intellihide and wnck loaded
        if self.cfg['auto_hide'] == 2 and not self.wnck:
            # no wnck module ? fallback to autohide
            core.logINFO('intellihide : no wnck module found .. fallback to autohide', 'bar')
            self.cfg['auto_hide'] = 1
            self.wnck = None

        self.zoom_size = self.cfg['icon_size'] * self.cfg['zoom_factor'] * 1.0

        # timer for leave_bar callback
        self.timer_auto_hide = None
        # timer for smooth_hidding
        self.timer_smooth_hide = None

        # use for animate hiding
        self.moving = False
        self.count = 0
        self.countdown = 0
        self.timer_anim = None

        # middle click - Toggle always visible
        self.always_visible = False

        # launcher ( for mouseover/click )
        self.focus = None
        self.widget_pressed = False
        self.anim = 1
        self.fade = True
        self.anim_cpt = 0
        self.anim_flag = True

        # flag for plugin
        self.opened_popup = None
        self.lock_auto_hide = False

        ## convert color hex->rgb
        self.cfg['bg_color_rgb'] = core.hex2rgb(self.cfg['background_color'])
        self.cfg['border_color_rgb'] = core.hex2rgb(self.cfg['border_color'])
        self.cfg['bg_color_sub_rgb'] = core.hex2rgb(self.cfg['bg_color_sub'])
        self.cfg['border_color_sub_rgb'] = core.hex2rgb(self.cfg['border_color_sub'])
        self.cfg['bg_gradient_color_rgb'] = core.hex2rgb(self.cfg['background_gradient_color'])
        
        self.pixbuf_glow = gtk.gdk.pixbuf_new_from_file('images/pixmaps/button.png')
        self.pixbuf_pressed = gtk.gdk.pixbuf_new_from_file('images/pixmaps/launcher.png')

        ## Create main bar
        self.create_bar()
        self.set_below_or_above()

        ## tooltip
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

        if self.cfg['tooltips']:
            self.tooltip = ui.TooltipWindow(self)

        # create a new plugin manager
        self.plg_mgr = PluginManager(self)
        
        # and start to pack plugin ..
        for ind in self.cfg['ind_launcher']:
            self.plg_mgr.append(ind, self.launcher[ind])
        self.plg_mgr.run()

        # start bar callback
        self.init_bar_callback()

        ## FIXME!
        ## gtk.Window doesn't stick after reload config ?!
        self.win.realize()
        self.win.stick()
        self.reposition()
        self.win.show_all()

        # init all plugins
        self.plg_mgr.on_init()

        ## FIXME!!
        # sometimes reposition doesn't work :/ .. quick hack
        gobject.timeout_add(500, self.reposition)

        if DEBUG and not 1:
            for index in self.plg_mgr.index:
                print ('------------------------------------')
                for val in self.plg_mgr.plugins[index].settings:
                    print ('%s = %s' % (val, self.plg_mgr.plugins[index].settings[val]))

                print ('widget :', self.plg_mgr.plugins[index])
                print ('index :', self.plg_mgr.plugins[index].index)
                print ('------------------------------------\n')

    def set_below_or_above(self):
        if self.cfg['keep_below']:
            self.win.set_keep_below(True)
            self.win.set_keep_above(False)
        else:
            self.win.set_keep_above(True)
            self.win.set_keep_below(False)

    def reposition(self):
        if self.cfg['fixed_mode']:
            screen_width, screen_height = gtk.gdk.screen_width(), gtk.gdk.screen_height()
            
            if self.cfg['position'] == "bottom" or self.cfg['position'] == "top":
                req_size = int(screen_width * self.cfg['fixed_size']/100.0)
                self.win.resize(req_size, 1)
            else:
                req_size = int(screen_height * self.cfg['fixed_size']/100.0)
                self.win.resize(1, req_size)               
        else:
            self.win.resize(1, 1)

        self.bar_move()
        self.toggle_hidden()
        
        # Intellihide
        if self.wnck:
            self.check_window_state()
            
        self.update()
        return False

    def expose(self, widget, event):
        if self.is_composited:
            cr = self.win.window.cairo_create()
            ## Full transparent window
            cr.set_source_rgba(0, 0, 0, 0)
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()
        else:
            self.opacity = 1
            x, y, width, height = self.win.get_allocation()
            pixmap = gtk.gdk.Pixmap(None, width, height, 1)
            cr = pixmap.cairo_create()
            # Clear the bitmap to False
            cr.set_source_rgb(0, 0, 0)
            cr.set_operator(cairo.OPERATOR_DEST_OUT)
            cr.paint()
            ## Draw next over 
            cr.set_operator(cairo.OPERATOR_OVER)
            
            rect = self.win.get_allocation()
            cr.set_source_rgb(1, 1, 1)

            if self.cfg['bar_style'] == 0:      # Edgy
                draw.rounded_rect2(cr, rect, self.cfg['rounded_corner'],
                                       self.cfg['position'], fill=True)
            elif self.cfg['bar_style'] == 1:    # Floaty
                draw.rounded_rect(cr, rect, self.cfg['rounded_corner'], 
                                       self.cfg['position'], fill=True)
            else:
                draw.rounded_rect(cr, rect, 0, self.cfg['position'], fill=True)

            self.win.shape_combine_mask(pixmap, 0, 0)
            cr = self.win.window.cairo_create()
            
        if (self.bar_hidden and self.cfg['fade_hidden']) or not self.init_flag:
            return False

        ## Draw next over 'transparent window'
        cr.set_operator(cairo.OPERATOR_OVER)

        ## paint background
        cr.set_source_surface(self.bg_surface, 0, 0)
        cr.paint()

        if DEBUG:
            x, y, width, height = self.win.get_allocation()
            cr.set_source_rgb(1, 0.2, 0.2)
            cr.set_line_width(1)
            cr.rectangle(x, y, width, height)
            cr.stroke()
            x, y, width, height = self.plg_mgr.box.get_allocation()
            cr.set_source_rgb(0.2, 1, 0.2)
            cr.set_line_width(1)
            cr.rectangle(x, y, width, height)
            cr.stroke()

        return False

    def draw_bg(self):
        if self.cfg['bar_style'] == 3 and not self.is_composited: 
            self.cfg['bar_style'] == 2
            
        if not self.is_composited:
            self.opacity = 1
        else:
            self.opacity = self.cfg['opacity']/100.0
            
        cr = cairo.Context(self.bg_surface)
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_line_width(1)

        if self.bar_hidden or not self.is_composited:
            rect = self.win.get_allocation()
        else:
            rect = self.draw_x, self.draw_y, self.draw_width, self.draw_height

        cr.save()

        r, g, b = self.cfg['bg_color_rgb']
        cr.set_source_rgba(r, g, b, self.opacity)
        
        if self.cfg['bar_style'] == 0:      # Edgy
            draw.rounded_rect2(cr, rect, self.cfg['rounded_corner'], self.cfg['position'], fill=True)
        elif self.cfg['bar_style'] == 1:    # Floaty
            draw.rounded_rect(cr, rect, self.cfg['rounded_corner'], self.cfg['position'], fill=True)
        elif self.cfg['bar_style'] == 2:    # 3d
            draw.trapeze(cr, rect, self.cfg['rounded_corner'], self.cfg['position'], fill=True)

        if self.cfg['bg_gradient']:
            r1, g1, b2 = self.cfg['bg_gradient_color_rgb']
            lg = draw.gradient_color2trans(r1, g1, b2, rect, self.opacity, self.cfg['position'], invert=False)
            cr.set_source(lg)

            if self.cfg['bar_style'] == 0:      # Edgy
                draw.rounded_rect2(cr, rect, self.cfg['rounded_corner'], self.cfg['position'], fill=True)
            elif self.cfg['bar_style'] == 1:    # Floaty
                draw.rounded_rect(cr, rect, self.cfg['rounded_corner'], self.cfg['position'], fill=True)
            elif self.cfg['bar_style'] == 2:    # 3d
                draw.trapeze(cr, rect, self.cfg['rounded_corner'], self.cfg['position'], fill=True)

        if self.cfg['show_border']:
            r, g, b = self.cfg['border_color_rgb']
            cr.set_source_rgba(r, g, b, self.opacity)
            rect = rect[0]+1, rect[1]+1, rect[2]-2, rect[3]-2

            if self.cfg['bar_style'] == 0:      # Edgy
                draw.rounded_rect2(cr, rect, self.cfg['rounded_corner'], self.cfg['position'])
            elif self.cfg['bar_style'] == 1:    # Floaty
                draw.rounded_rect(cr, rect, self.cfg['rounded_corner'], self.cfg['position'])
            elif self.cfg['bar_style'] == 2:    # 3d
                draw.trapeze(cr, rect, self.cfg['rounded_corner'], self.cfg['position'])

    def init_bar_pos(self):

        self.bar_width , self.bar_height = self.win.get_size()
        screen_width, screen_height = gtk.gdk.screen_width(), gtk.gdk.screen_height()

        if not self.is_composited:
            bar_size = 1
        else:
            bar_size = self.cfg['bar_size']/100.0

        if self.cfg['position'] == "bottom":
            if self.cfg['bar_style'] == 0:
                self.bar_pos_y = screen_height - self.bar_height + 1
            else:
                self.bar_pos_y = screen_height - self.bar_height - self.cfg['offset_pos']
                
            if self.cfg['align'] == "start":
                self.bar_pos_x = 0 + self.cfg['offset_align']
            elif self.cfg['align'] == "center":
                self.bar_pos_x = ( screen_width - self.bar_width ) // 2
            elif self.cfg['align'] == "end":
                self.bar_pos_x = screen_width - self.bar_width - self.cfg['offset_align']

            self.bar_hide_y = screen_height - self.cfg['hidden_size']
            self.bar_hide_x = self.bar_pos_x

            ## for expose
            self.draw_height = (2*self.cfg['padding']+self.cfg['icon_size'])*bar_size
            self.draw_width = self.bar_width
            self.draw_x = 0
            self.draw_y = self.bar_height - (2*self.cfg['padding']+self.cfg['icon_size'])*bar_size

        elif self.cfg['position'] == "top":
            if self.cfg['bar_style'] == 0:
                self.bar_pos_y = -1
            else:
                self.bar_pos_y = self.cfg['offset_pos']
                
            if self.cfg['align'] == "start":
                self.bar_pos_x = self.cfg['offset_align']
            elif self.cfg['align'] == "center":
                self.bar_pos_x = ( screen_width - self.bar_width ) // 2
            elif self.cfg['align'] == "end":
                self.bar_pos_x = screen_width - self.bar_width - self.cfg['offset_align']

            self.bar_hide_y = self.cfg['hidden_size'] - self.bar_height
            self.bar_hide_x = self.bar_pos_x

            ## for expose
            self.draw_height = (2*self.cfg['padding']+self.cfg['icon_size'])*bar_size
            self.draw_width = self.bar_width
            self.draw_x, self.draw_y = 0, 0

        elif self.cfg['position'] == "left":
            if self.cfg['bar_style'] == 0:
                self.bar_pos_x = -1
            else:
                self.bar_pos_x = self.cfg['offset_pos']
                
            if self.cfg['align'] == "start":
                self.bar_pos_y = 0 + self.cfg['offset_align']
            elif self.cfg['align'] == "center":
                self.bar_pos_y = (screen_height - self.bar_height) // 2
            elif self.cfg['align'] == "end":
                self.bar_pos_y = screen_height - self.bar_height - self.cfg['offset_align']

            self.bar_hide_y = self.bar_pos_y
            self.bar_hide_x = - self.bar_width + self.cfg['hidden_size']

            ## for expose
            self.draw_height = self.bar_height
            self.draw_width = (2*self.cfg['padding']+self.cfg['icon_size'])*bar_size
            self.draw_x, self.draw_y = 0, 0

        elif self.cfg['position'] == "right":
            if self.cfg['bar_style'] == 0:
                self.bar_pos_x = screen_width - self.bar_width +1
            else:
                self.bar_pos_x = screen_width - self.bar_width - self.cfg['offset_pos']
                
            if self.cfg['align'] == "start":
                self.bar_pos_y = 0 + self.cfg['offset_align']
            elif self.cfg['align'] == "center":
                self.bar_pos_y = (screen_height - self.bar_height) // 2
            elif self.cfg['align'] == "end":
                self.bar_pos_y = screen_height - self.bar_height - self.cfg['offset_align']

            self.bar_hide_y = self.bar_pos_y
            self.bar_hide_x = screen_width - self.cfg['hidden_size']

            ## for expose
            self.draw_height = self.bar_height
            self.draw_width = (2*self.cfg['padding']+self.cfg['icon_size'])*bar_size
            self.draw_x = self.bar_width - (2*self.cfg['padding']+self.cfg['icon_size'])*bar_size
            self.draw_y = 0

        self.draw_width = int(self.draw_width)
        self.draw_height = int(self.draw_height)
        self.draw_x = int(self.draw_x)
        self.draw_y = int(self.draw_y)

        self.bg_surface = cairo.ImageSurface (cairo.FORMAT_ARGB32, self.bar_width , self.bar_height)
        self.draw_bg()
        self.init_flag = True

    def launcher_leave_notify(self, plugin, event):
        plugin.focus = False
        self.anim_flag = True
        self.update()

        if self.cfg['tooltips']:
            self.tooltip.stop()

    def widget_enter_notify(self, plugin, event):
        plugin.focus = True

        ## tooltip
        if plugin.has_tooltip and self.cfg['tooltips']:
            self.tooltip.run(plugin)

        self.anim = 1
        self.anim_cpt = 0
        self.bar_enter_notify()
        self.update()
        return True

    def widget_press(self, widget, event):
        if event.button==1:
            widget.is_pressed = True
            self.update()

        if self.cfg['tooltips']:
            self.tooltip.stop()
        
        if event.button==2:
            return False

    def widget_released(self, widget, event):
        if event.button==1:
            widget.onClick(widget, event)
            widget.is_pressed = False
            self.update()

        if event.button==2:
            return False
            
    def update(self):
        self.win.queue_draw()
        return True

    def update_all(self):
        self.init_bar_pos()
        self.set_geometry()
        self.reposition()
        self.draw_bg()
        self.update() 

    def check_window_state(self):
        if not self.init_flag:
            return
        
        if not (self.cfg['auto_hide'] == 2 and self.wnck):
            return

        if self.wnck.current_state and not self.bar_hidden and not self.always_visible:
            self.bar_hide()
        elif self.bar_hidden and not self.wnck.current_state:
            self.bar_hidden = False
            self.bar_move()

    def bar_move(self):
        if self.bar_hidden:
            self.win.move(self.bar_hide_x, self.bar_hide_y)
        else:
            self.win.move(self.bar_pos_x, self.bar_pos_y)
        self.update()
        self.update_strut(self.win)

    def toggle_hidden(self, widget=None , event=None):
        if  self.bar_hidden:
            self.bar_hidden = False
            self.bar_move()
        elif self.cfg['auto_hide'] == 1: # autohide
            self.bar_hide()
        elif self.cfg['auto_hide'] == 2: # intellihide
            self.check_window_state()

    def bar_hide(self):
        if not self.can_hide:
            return
        if self.cfg['smooth_hide']:
            self.count = 14 ## 500 / 35 ms
            self.countdown = self.count
            self.moving = True
            self.timer_smooth_hide = gobject.timeout_add(35, self.on_timeout_hide)
        else:
            self.bar_hidden = True
            self.bar_move()

    def on_timeout_hide(self):
        self.countdown -= 1
        N = self.count
        n = self.countdown
        x = self.bar_pos_x + ( (self.bar_hide_x - self.bar_pos_x) // N ) * (N-n)

        if self.cfg['position'] == "top":
            y =  ( (self.bar_hide_y - self.bar_pos_y ) / N ) * (N-n)
        else:
            y = self.bar_pos_y + ( (self.bar_hide_y - self.bar_pos_y ) // N ) * (N-n)

        self.win.move(x, y)
        if self.countdown <= 0:
            self.bar_hidden = True
            self.bar_move()
            self.moving = False
            return False
        else:
            return True

    def bar_leave_notify(self, widget=None, event=None):
        if not self.timer_auto_hide == None:
            gobject.source_remove(self.timer_auto_hide)
            self.timer_auto_hide = None

        if (self.cfg['auto_hide'] == 1 or self.wnck) and self.can_hide and not self.always_visible:
            if self.cfg['timer'] == 0:
                ## minimum time because bar auto-hide it-self :(
                if self.cfg['offset_pos'] > 0:
                    self.timer_auto_hide = gobject.timeout_add(500, self.on_timeout_notify)
                else:
                    self.timer_auto_hide = gobject.timeout_add(100, self.on_timeout_notify)
            else:
                self.timer_auto_hide = gobject.timeout_add(self.cfg['timer']*1000, self.on_timeout_notify)

        self.focus = None
        self.mouse_over = False
        self.update()
        
        if self.cfg['tooltips']:
            self.tooltip.stop()
        return True

    def bar_enter_notify(self, widget=None, event=None):
        if self.cfg['auto_raise'] and self.bar_hidden:
            self.toggle_hidden()

        if not self.timer_auto_hide == None:
            gobject.source_remove(self.timer_auto_hide)
            self.timer_auto_hide = None

        if self.moving:
            self.moving = False
            self.bar_hidden = True
            gobject.source_remove(self.timer_smooth_hide)
            self.timer_smooth_hide = None
            self.toggle_hidden()

        self.mouse_over = True

    def bar_released(self, widget, event):
        ## FIXME! avoid double callback (I don't know why I receive twice)
        if self.last_event_time == event.time:
            return False
        self.last_event_time = event.time

        if event.button==3: # right click
            #~ if event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK:
            self.popupMenu.popup(None, None, None, event.button, event.time)

        elif event.button==2: # middle click
            self.always_visible = not self.always_visible

        elif event.button==1 and self.bar_hidden: # left click
            self.toggle_hidden()

    def on_timeout_notify(self):
        ## autohide
        if self.cfg['auto_hide'] == 1 and not self.bar_hidden:
            self.toggle_hidden()
        ## intellihide
        elif self.wnck:
            self.check_window_state()

        if self.timer_auto_hide:
            gobject.source_remove(self.timer_auto_hide)
        self.timer_auto_hide = None
        return False

    def edit_config(self, widget):
        if not self.bar_conf:
            self.bar_conf = barconf.Conf(self)
        else:
            self.bar_conf.window.present()

    def doquit(self, widget=None, data=None):
        ## FIXME!! what to do now ? try to close adeskbar nicely ..
        self.win.hide()
        for ind in self.plg_mgr.plugins:
            self.plg_mgr.plugins[ind].stop()
        self.win.destroy()
        gtk.main_quit()

    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt: 
            # ctrl-c
            ## FIXME!! what to do now ? try to close adeskbar nicely ..
            self.doquit()

class PluginManager:
    """ Class AppManager - load/resize plugins for main bar """
    
    def __init__( self, bar ):
        """ configure container for plugins """

        self.bar = bar
        self.index = []
        self.plugins = {}

        if bar.cfg['position'] == "top" or bar.cfg['position'] == "bottom":
            self.box = gtk.HBox(False, bar.cfg['icon_space'])
        else:
            self.box = gtk.VBox(False, bar.cfg['icon_space'])

        self.spacer_left_top = gtk.EventBox()
        self.spacer_left_bottom = gtk.EventBox()
        self.spacer_right = gtk.EventBox()
        
        if not DEBUG:
            self.spacer_left_top.set_visible_window(False)
            self.spacer_left_bottom.set_visible_window(False)
            self.spacer_right.set_visible_window(False)

        self.table = gtk.Table(3, 3, False)
        self.table.set_row_spacings(0)
        self.table.set_col_spacings(0)

        self.table.attach(self.spacer_left_top, 0, 1, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        self.table.attach(self.spacer_left_bottom, 0, 1, 2, 3, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        self.table.attach(self.spacer_right, 2, 3, 0, 1, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        
        if self.bar.cfg['fixed_mode']:
            self.table.attach(self.box, 1, 2, 1, 2, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)
        else:
            self.table.attach(self.box, 1, 2, 1, 2, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)

        bar.win.add(self.table)
        self.resize_spacer()
        self.table.show_all()

        self.box_alloc = self.box.get_allocation()

    def remove(self, index):
        self.index.remove(index)
        self.plugins[index].hide()
        self.plugins[index].destroy()
        self.plugins.pop(index)
        self.bar.reposition()

    def reorder(self, widget, position):
        self.box.reorder_child(widget, position)

    def on_init(self):
        for index in self.plugins:
            self.plugins[index].on_init()

    def run(self):
        #~ if not self.bar.cfg['fixed_mode']:
        self.box.connect('size-allocate', self.box_size_allocate)

    def box_size_allocate(self, widget, allocation):
        """ resize to minimum size and reposition """
        if not self.box_alloc == allocation:
            self.box.set_size_request(-1, -1)
            self.bar.win.resize(1, 1)
            gobject.idle_add(self.bar.reposition)

        self.box_alloc = allocation

    def resize_spacer(self):
        """ configure main bar aspect from config """
        cfg = self.bar.cfg
        
        padding = cfg['padding']
        size, zoom_f, space = cfg['icon_size'], cfg['zoom_factor'], cfg['icon_space']
        offset_top = max( padding, int(size * zoom_f - size) )
        offset_side = 2*padding

        if cfg['position']=='bottom':
            self.spacer_left_top.set_size_request(offset_side, offset_top)
            self.spacer_left_bottom.set_size_request(offset_side, padding)
            self.spacer_right.set_size_request(offset_side, padding)

        elif cfg['position']=='top':
            self.spacer_left_top.set_size_request(offset_side, padding)
            self.spacer_left_bottom.set_size_request(offset_side, offset_top)
            self.spacer_right.set_size_request(offset_side, padding)

        elif cfg['position']=='left':
            self.spacer_left_top.set_size_request(padding, offset_side)
            self.spacer_left_bottom.set_size_request(padding, offset_side)
            self.spacer_right.set_size_request(offset_top, offset_side)

        elif cfg['position']=='right':
            self.spacer_left_top.set_size_request(offset_top, offset_side)
            self.spacer_left_bottom.set_size_request(offset_top, offset_side)
            self.spacer_right.set_size_request(padding, offset_side)

    def load_plugin(self, p, settings=None):
        """ load plugin as widget """
        try:
            core.logINFO(("Loading plugin '%s' ..") % (p), 'bar')
            exec("import plugins.%s as plugin" % p)
            widget = plugin.Plugin(self.bar, settings)
        except Exception as e:
            core.logINFO(("EE : Unable to load plugin '%s': %s") % (p, e), 'bar')
            traceback.print_exc()
            return None
        return widget

    def append(self, index, settings):
        """ append plugin (widget) to main bar """

        is_plugin = False
        is_separator = False

        if len(settings['cmd']) > 1 and settings['cmd'][0] == '@':
            is_plugin = True

            if settings['cmd'][1:] == 'separator':
                is_separator = True

            elif settings['cmd'][1:] == 'drawer':
                if index in self.bar.drawer:
                    settings['launcher'] = self.bar.drawer[index]
                else:
                    settings['launcher'] = {}

            widget = self.load_plugin(settings['cmd'][1:], settings)

        else:
            widget = self.load_plugin('launcher', settings)

        if widget: # load OK
            widget.tooltip = settings['name']
            widget.index = index

            if widget.can_show_icon:
                widget.set_icon(settings['icon'], is_separator)

            widget.resize()
            widget.connect("button-release-event", self.bar.widget_released)
            widget.connect("button-press-event", self.bar.widget_press)
            widget.connect("enter-notify-event", self.bar.widget_enter_notify)
            widget.connect("leave-notify-event", self.bar.launcher_leave_notify)

            widget.show()

            if settings['cmd'][1:] == 'tasklist':
                self.box.pack_start(widget, True, True)
            else:
                self.box.pack_start(widget, False, False)

            self.index.append(index)
            self.plugins[index] = widget
            return widget
        else:
            return None        

    def set_orientation(self):
        if self.bar.cfg['position'] == "top" or self.bar.cfg['position'] == "bottom":
            self.box.set_orientation(gtk.ORIENTATION_HORIZONTAL)
        else:
            self.box.set_orientation(gtk.ORIENTATION_VERTICAL)

    def set_panel_mode(self):
        self.table.remove(self.box)
        if self.bar.cfg['fixed_mode']:
            self.table.attach(self.box, 1, 2, 1, 2, xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.EXPAND|gtk.FILL)
        else:
            self.table.attach(self.box, 1, 2, 1, 2, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
