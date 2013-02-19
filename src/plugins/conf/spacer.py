# -*- coding: utf-8 -*-

import gtk

settings = { 
    'size':4,
    }

class config(gtk.Frame):
    def __init__(self, conf, ind):
        gtk.Frame.__init__(self)
        self.conf = conf
        self.ind = ind
        
        self.settings = conf.launcher[ind]

        self.set_border_width(5)
        framebox = gtk.HBox(False, 0)
        framebox.set_border_width(5)
        framebox.set_spacing(10)
        self.add(framebox)

        for key in settings:
            if not self.settings.has_key(key):
                self.settings[key] = settings[key]

        label = gtk.Label('Size')
        label.set_alignment(0.9, 0.5)
        
        adjustment = gtk.Adjustment(value=self.settings['size'], lower=1, upper=128, step_incr=1, page_incr=8, page_size=0)
        self.size = gtk.SpinButton(adjustment=adjustment, climb_rate=0.0, digits=0)
        self.size.set_tooltip_text('size in pixel')

        framebox.pack_start(label, True)
        framebox.pack_start(self.size, False)

    def save_change(self):
        self.settings['size'] = int(self.size.get_value())
        self.conf.plg_mgr.plugins[self.ind].restart()

