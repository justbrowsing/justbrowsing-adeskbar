import gtk

settings = {'terminal':'x-terminal-emulator', 'show_label':1}

class config(gtk.Frame):
    def __init__(self, conf, ind):
        gtk.Frame.__init__(self)
        self.conf = conf
        self.ind = ind

        self.set_border_width(5)
        framebox = gtk.HBox(False, 0)
        framebox.set_border_width(5)
        framebox.set_spacing(10)
        self.add(framebox)

        for key in settings:
            if not key in conf.launcher[ind]:
                conf.launcher[ind][key] = settings[key]

        self.settings = conf.launcher[ind]
        if self.settings['show_label'] in ('False','false','0', 0):
            self.settings['show_label'] = 0
        else:
            self.settings['show_label'] = 1

        self.show_label_checkbox = gtk.CheckButton('Show label')
        self.show_label_checkbox.set_active(self.settings['show_label'])

        label = gtk.Label("Terminal :")
        label.set_alignment(0, 0.5)
        self.terminal = gtk.Entry()
        self.terminal.set_width_chars(20)
        self.terminal.set_text(conf.launcher[ind]['terminal'])

        framebox.pack_start(self.show_label_checkbox)
        framebox.pack_start(label)
        framebox.pack_end(self.terminal)

    def save_change(self):
        self.conf.launcher[self.ind]['terminal'] = self.terminal.get_text()
        self.conf.launcher[self.ind]['show_label'] = int(self.show_label_checkbox.get_active())
        self.conf.plg_mgr.plugins[self.ind].restart()
        
