# -*- coding: utf-8 -*-

##
#   ADesk Bar - config
##

import os
import sys
import adesk.core as Core

def read(cfg_file):
    Core.logINFO("read ..", 'config')
    CONFIG = {}
    LAUNCHER = {}
    DRAWER = {}
    
    CONFIG['ind_launcher'] = []
    
    ## FIXME! default connfig
    CONFIG['fade_hidden']=False
    CONFIG['icon_space']=10
    CONFIG['show_border']=1
    CONFIG['smooth_hide']=1
    CONFIG['background_color']="#333333"
    CONFIG['bg_color_sub']="#EEEEEE"
    CONFIG['border_color_sub']="#7F7F7F"
    CONFIG['bar_size']=100
    CONFIG['rounded_corner']=15
    CONFIG['icon_size']=36
    CONFIG['hidden_size']=5
    CONFIG['opacity']=70
    CONFIG['border_color']="#313335"
    CONFIG['padding']=4
    CONFIG['zoom_factor']=1.2
    CONFIG['keep_below']=False
    CONFIG['offset_pos']=4
    CONFIG['align']="center"
    CONFIG['timer']=1
    CONFIG['bg_gradient']=True
    CONFIG['auto_hide']=2
    CONFIG['auto_raise']=1
    CONFIG['offset_align']=0
    CONFIG['position']="bottom"
    CONFIG['tooltips']=True
    CONFIG['fixed_size']=100
    CONFIG['fixed_mode']=True
    CONFIG['reserve_space']=False

    ## new in v0.3.9
    CONFIG['background_gradient_color']="#333333"
    ## new in v0.4
    CONFIG['bar_style']=0
    CONFIG['icons_effects']=3
    
    
    home = os.environ['HOME']

    ## custom config
    if os.access("%s/.config/adeskbar/%s.cfg" % (home, cfg_file), os.F_OK|os.R_OK):
        Core.logINFO("config = %s/.config/adeskbar/%s.cfg" % (home, cfg_file), 'config')
        conf_path = "%s/.config/adeskbar/%s.cfg" % (home, cfg_file)

    ## read default config
    elif os.access("default.cfg", os.F_OK|os.R_OK):
        Core.logINFO("config = default.cfg", 'config')
        conf_path = 'default.cfg'

    ## no config ? exit !
    else:
        Core.logINFO("ERROR : can't read config !!!", 'config')
        #~ Core.show_msg("Sorry, but can't read config !!!")
        sys.exit()
    del home

    f = open(conf_path,'r')

    current_cat = None
    current_sub = None
    error_config = False

    for line in f:
        if line == '\n' or line[0]=='#':
            continue
        try:
            line = line.strip('\n')

            ## check if is a category
            if line[0] == '[':
                current_cat = line[1:-1]
                if '/' in current_cat:
                    tmp = current_cat.split('/')
                    current_cat = tmp[0]
                    current_sub = tmp[1]
                    if current_cat == 'LAUNCHER':
                        LAUNCHER[current_sub] = {}
                        CONFIG['ind_launcher'].append(current_sub)
                else:
                    current_sub = None
                continue

            if current_cat == 'CONFIG':
                tmp = line.split('=',1)
                key = tmp[0]
                CONFIG[key] = tmp[1]

            elif current_cat == 'LAUNCHER':
                tmp = line.split('=',1)
                key = tmp[0]
                LAUNCHER[current_sub][key] = tmp[1]

            elif current_cat == 'DRAWER':
                (cmd, icon, desc) = line.split('##')
                if not current_sub in DRAWER:
                    DRAWER[current_sub] = []
                DRAWER[current_sub].append((cmd.strip(), icon.strip(), desc.strip()))

        except Exception, e:
            traceback.print_exc()
            error_config = True

    f.close()

    ## convert value : str -> int
    for key in ('padding','icon_size','offset_pos','offset_align','bar_style',
                'rounded_corner','hidden_size','opacity','timer', 
                'icons_effects','bar_size','icon_space','auto_hide'):
        CONFIG[key] = int(CONFIG[key])

    ## convert value : str -> True / False
    for key in ('auto_raise','smooth_hide', 'tooltips', 
                'show_border','fade_hidden', 'fixed_mode', 'reserve_space',
                'keep_below','bg_gradient'):

        if CONFIG[key] in ('true','True','1','yes'):
            CONFIG[key] = True
        else:
            CONFIG[key] = False

    CONFIG['bg_color_rgb'] = Core.hex2rgb(CONFIG['background_color'])
    CONFIG['border_color_rgb'] = Core.hex2rgb(CONFIG['border_color'])

    if CONFIG['hidden_size'] < 1:
        CONFIG['hidden_size'] = 1

    CONFIG['zoom_factor'] = float(CONFIG['zoom_factor'])
    CONFIG['fixed_size'] = float(CONFIG['fixed_size'])

    if error_config:
        ## FIXME!!
        pass
        #~ adesk.show_msg("Error while loading user config .. ( old config file ? )")

    return CONFIG, LAUNCHER, DRAWER

def save(cfg_file, config_data, ind_launcher, launchers, drawers):
    """ save config to file"""
    Core.logINFO("save ..", 'config')

    str_cfg = '## ADeskBar config\n'

    str_cfg += '[CONFIG]\n'
    for item in config_data:
        val = config_data[item]
        str_cfg += str(item) + "=" + str(val) + '\n'

    str_cfg += '\n'

    for ind in ind_launcher:
        str_cfg += '[LAUNCHER/%s]\n' % ind
        if 'launcher' in launchers[ind]:
            launchers[ind].pop('launcher')
        for key in launchers[ind]:
            str_cfg += '%s=%s\n' % (key, launchers[ind][key])
        str_cfg += '\n'

    str_cfg += '\n'

    for ind in drawers:
        str_cfg += '[DRAWER/%s]\n' % ind
        for drawer in drawers[ind]:
            str_cfg += "%s##%s##%s\n" % (drawer[0], drawer[1], drawer[2])
        str_cfg += '\n'

    str_cfg += '\n'

    home = os.environ['HOME']
    if not os.path.exists("%s/.config/adeskbar" % home):
        os.makedirs("%s/.config/adeskbar" % home)

    if cfg_file==None or cfg_file=='None':
        cfg_file = 'default'

    src = "%s/.config/adeskbar/%s.cfg" % (home,cfg_file)

    configfile =  open(src, 'w')
    configfile.write(str_cfg)
    configfile.close()
