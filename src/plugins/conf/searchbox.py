import gtk

settings = {'browser':'x-www-browser', 'engine':'http://www.google.com/search?q='}

class config(gtk.Frame):
    def __init__(self, conf, ind):
        gtk.Frame.__init__(self)
        self.conf = conf
        self.ind = ind

        self.set_border_width(5)
        framebox = gtk.VBox(False, 0)
        framebox.set_border_width(5)
        framebox.set_spacing(10)
        self.add(framebox)

        for key in settings:
            if not key in conf.launcher[ind]:
                conf.launcher[ind][key] = settings[key]

        self.settings = conf.launcher[ind]

        table = gtk.Table(2, 2, False)

        label = gtk.Label("Browser :")
        label.set_alignment(0, 0.5)
        self.browser = gtk.Entry()
        #~ self.browser.set_width_chars(20)
        self.browser.set_text(self.settings['browser'])
        table.attach(label, 0, 1, 0, 1)
        table.attach(self.browser, 1, 2, 0, 1)

        label = gtk.Label("Engine :")
        label.set_alignment(0, 0.5)
        self.engine = gtk.Entry()
        #~ self.engine.set_width_chars(20)
        self.engine.set_text(self.settings['engine'])
        table.attach(label, 0, 1, 1, 2)
        table.attach(self.engine, 1, 2, 1, 2)

        framebox.pack_start(table)

    def save_change(self):
        self.conf.launcher[self.ind]['browser'] = self.browser.get_text()
        self.conf.launcher[self.ind]['engine'] = self.engine.get_text()
