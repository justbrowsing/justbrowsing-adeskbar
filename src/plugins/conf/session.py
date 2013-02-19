import gtk

settings = {
    'lockscreen':'xscreensaver-command -lock',
    'logout':'openbox --exit',
    'hibernate':'',
    'suspend':'',
    'reboot':'dbus-send --system --print-reply --dest="org.freedesktop.Hal" /org/freedesktop/Hal/devices/computer org.freedesktop.Hal.Device.SystemPowerManagement.Reboot',
    'shutdown':'dbus-send --system --print-reply --dest="org.freedesktop.Hal" /org/freedesktop/Hal/devices/computer org.freedesktop.Hal.Device.SystemPowerManagement.Shutdown',
    'show_label':True,
    'icon_size':32,
    }

class config(gtk.Frame):
    def __init__(self, conf, ind):
        gtk.Frame.__init__(self)
        self.conf = conf
        self.ind = ind

        for key in settings:
            if not key in conf.launcher[ind]:
                conf.launcher[ind][key] = settings[key]

        self.set_border_width(5)
        framebox = gtk.VBox(False, 0)
        framebox.set_border_width(5)
        framebox.set_spacing(10)
        self.add(framebox)


        optionbox = gtk.HBox(False, 0)
        optionbox.set_border_width(0)
        optionbox.set_spacing(10)
        framebox.pack_start(optionbox, False, False)
        framebox.pack_start(gtk.HSeparator(), False, False)

        self.show_label_checkbox = gtk.CheckButton('Show label')
        self.show_label_checkbox.set_active(conf.launcher[ind]['show_label'])

        adjustment = gtk.Adjustment(value=conf.launcher[ind]['icon_size'], lower=16, upper=128, step_incr=1, page_incr=8, page_size=0)
        self.icon_size = gtk.SpinButton(adjustment=adjustment, climb_rate=0.0, digits=0)
        self.icon_size.set_tooltip_text('icon size in pixel')
        
        label = gtk.Label('icon size')
        
        optionbox.pack_start(self.show_label_checkbox, False, False)
        optionbox.pack_end(self.icon_size, False, False)
        optionbox.pack_end(label, False, False)

        table = gtk.Table()
        framebox.pack_start(table, False, False)

        label = gtk.Label("Lock screen  :")
        label.set_alignment(0, 0.5)
        self.lockscreen = gtk.Entry()
        self.lockscreen.set_width_chars(45)
        self.lockscreen.set_text(conf.launcher[ind]['lockscreen'])

        table.attach(label, 0, 1, 0, 1)
        table.attach(self.lockscreen, 1, 2, 0, 1)

        label = gtk.Label("Log Out  :")
        label.set_alignment(0, 0.5)
        self.logout = gtk.Entry()
        self.logout.set_width_chars(45)
        self.logout.set_text(conf.launcher[ind]['logout'])

        table.attach(label, 0, 1, 1, 2)
        table.attach(self.logout, 1, 2, 1, 2)


        label = gtk.Label("Hibernate  :")
        label.set_alignment(0, 0.5)
        self.hibernate = gtk.Entry()
        self.hibernate.set_width_chars(45)
        self.hibernate.set_text(conf.launcher[ind]['hibernate'])

        table.attach(label, 0, 1, 2, 3)
        table.attach(self.hibernate, 1, 2, 2, 3)


        label = gtk.Label("Suspend  :")
        label.set_alignment(0, 0.5)
        self.suspend = gtk.Entry()
        self.suspend.set_width_chars(45)
        self.suspend.set_text(conf.launcher[ind]['suspend'])

        table.attach(label, 0, 1, 3, 4)
        table.attach(self.suspend, 1, 2, 3, 4)


        label = gtk.Label("Reboot  :")
        label.set_alignment(0, 0.5)
        self.reboot = gtk.Entry()
        self.reboot.set_width_chars(45)
        self.reboot.set_text(conf.launcher[ind]['reboot'])

        table.attach(label, 0, 1, 4, 5)
        table.attach(self.reboot, 1, 2, 4, 5)


        label = gtk.Label("Shutdown  :")
        label.set_alignment(0, 0.5)
        self.shutdown = gtk.Entry()
        self.shutdown.set_width_chars(45)
        self.shutdown.set_text(conf.launcher[ind]['shutdown'])

        table.attach(label, 0, 1, 5, 6)
        table.attach(self.shutdown, 1, 2, 5, 6)

    def save_change(self):
        self.conf.launcher[self.ind]['lockscreen'] = self.lockscreen.get_text()
        self.conf.launcher[self.ind]['logout'] = self.logout.get_text()
        self.conf.launcher[self.ind]['hibernate'] = self.hibernate.get_text()
        self.conf.launcher[self.ind]['suspend'] = self.suspend.get_text()
        self.conf.launcher[self.ind]['reboot'] = self.reboot.get_text()
        self.conf.launcher[self.ind]['shutdown'] = self.shutdown.get_text()
        self.conf.launcher[self.ind]['icon_size'] = int(self.icon_size.get_value())
        self.conf.launcher[self.ind]['show_label'] = int(self.show_label_checkbox.get_active())
        self.conf.plg_mgr.plugins[self.ind].restart()
