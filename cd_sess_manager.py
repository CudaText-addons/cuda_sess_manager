﻿''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.0.2 2016-03-04'
'''
import  os, json, configparser, itertools
import  cudatext     as app
import  cudatext_cmd as cmds
import  cudax_lib    as apx
#from    .cd_plug_lib    import *

pass;                           LOG     = (-1==-1)  # Do or dont logging.
pass;                           from pprint import pformat
pass;                           pf=lambda d:pformat(d,width=150)

CDSESS_EXT      = '.cuda-session'
SWSESS_EXT      = '.synw-session'
SESS_JSON       = os.path.join(app.app_path(app.APP_DIR_SETTINGS), 'cuda_sess_manager.json')

# Localization
NEED_NEWER_API  = 'Plugin needs newer app version'
NO_RECENT       = 'No recent sessions'
NO_PREV         = 'No previous session'
SAVED           = 'Session "{stem}" is saved'
OPENED          = 'Session "{stem}" is opened'
CREATE_ASK      = 'Session "{stem}" not found\n\nCreate it?'
CREATED         = 'Session "{stem}" is created'
DLG_ALL_FILTER  = 'CudaText sessions|*{}|SynWrite sessions|*{}|All files|*.*'.format(CDSESS_EXT, SWSESS_EXT)
DLG_CUD_FILTER  = 'CudaText sessions|*{}'.format(CDSESS_EXT)

class Command:
    def recent(self):
        ''' Show list, use user select '''
        if not _checkAPI(): return
        sess    = self._loadSess(existing=True)
        rcnt    = sess['recent']
        if 0==len(rcnt):
            return app.msg_status(NO_RECENT)
        ssmenu  = '\n'.join(('{}\t{}'.format(juststem(sfile), os.path.dirname(sfile))
                                for sfile in rcnt
                            ))
        ans     = app.dlg_menu(app.MENU_LIST, ssmenu)
        if ans is None: return
        self.open(rcnt[ans])

    def open(self, ssnew=None):
        ''' Open new session from file ssnew or after user asking '''
        if not _checkAPI(): return
#       in_dir      = app.app_path(app.APP_DIR_DATA)
        sscur       = app.app_path(app.APP_FILE_SESSION)
        if ssnew is None:
            ssnew   = app.dlg_file(is_open=True, filters=DLG_ALL_FILTER
                    , init_filename='!'     # '!' to disable check "filename exists"
                    , init_dir=     ''
                    )
        if ssnew is None: return
        if ssnew.endswith(SWSESS_EXT) and os.path.isfile(ssnew):
            # Import from Syn
            sssyn   = ssnew
            sscud   = ssnew[:-len(SWSESS_EXT)]+CDSESS_EXT
            if os.path.isfile(sscud):
                sscud   = app.dlg_file(is_open=False, filters=DLG_CUD_FILTER
                        , init_filename=os.path.basename(sscud)
                        , init_dir=     os.path.dirname( sscud)
                        )
                if not sscud: return
            if not import_syn_sess(sssyn, sscud): return
            ssnew   = sscud
            
        ssnew       = apx.icase(False,''
                    ,   ssnew.endswith(CDSESS_EXT)  , ssnew
                    ,   os.path.isfile(ssnew)       , ssnew
                    ,   True                        , ssnew+CDSESS_EXT
                    )
        if os.path.isfile(ssnew):
            # Open
            app.app_proc(app.PROC_SAVE_SESSION, sscur)
            app.app_proc(app.PROC_LOAD_SESSION, ssnew)
            app.app_proc(app.PROC_SET_SESSION,  ssnew)
            app.msg_status(OPENED.format(stem=juststem(ssnew)))
            self.top_sess(ssnew)
        else:
            # New
            if app.ID_NO==app.msg_box(CREATE_ASK.format(stem=juststem(ssnew)), app.MB_YESNO):   return
            app.app_proc(app.PROC_SAVE_SESSION, sscur)
            app.ed.cmd(cmds.cmd_FileCloseAll)
            app.app_proc(app.PROC_SET_SESSION,  ssnew)
            app.app_proc(app.PROC_SAVE_SESSION, ssnew)
            app.msg_status(CREATED.format(stem=juststem(ssnew)))
            self.top_sess(ssnew)

    def create(self):
#       ssnew   = app.dlg_input('Name for new session', '')
        ssnew   = app.dlg_file(is_open=False, filters=DLG_CUD_FILTER
                    , init_filename=''
                    , init_dir=     ''
                    )
        if ssnew is None:   return
        ssnew   = ssnew \
                    if ssnew.endswith(CDSESS_EXT) else \
                  ssnew+CDSESS_EXT
        sscur       = app.app_path(app.APP_FILE_SESSION)
        app.app_proc(app.PROC_SAVE_SESSION, sscur)
        app.ed.cmd(cmds.cmd_FileCloseAll)
        app.app_proc(app.PROC_SET_SESSION,  ssnew)
        app.app_proc(app.PROC_SAVE_SESSION, ssnew)
        app.msg_status(CREATED.format(stem=juststem(ssnew)))
        self.top_sess(ssnew)
        pass;                   LOG and log('ok',())

    def openPrev(self, recent_pos=1):
        ''' Open session that was opened before.
            Params
                recent_pos  Position in recent list
        '''
        if not _checkAPI(): return
        sess    = self._loadSess(existing=True)
        rcnt    = sess['recent']
        if len(rcnt)<1+recent_pos:
            return app.msg_status(NO_PREV)
        self.open(rcnt[recent_pos])

    def save(self):
        ''' Save cur session to file '''
        if not _checkAPI(): return
        sscur       = app.app_path(app.APP_FILE_SESSION)
        app.app_proc(app.PROC_SAVE_SESSION, sscur)
        app.msg_status(SAVED.format(stem=juststem(sscur)))
        self.top_sess(sscur)

    def saveAs(self):
        ''' Save cur session to new file '''
        if not _checkAPI(): return
        sscur       = app.app_path(app.APP_FILE_SESSION)
        pass;                   app.msg_status(sscur)
        (ssdir
        ,ssfname)   = os.path.split(sscur)
        ssfname     = ssfname.replace('.json', '')
        ssnew       = app.dlg_file(is_open=False, filters=DLG_CUD_FILTER
                    , init_filename=ssfname
                    , init_dir=     ssdir
                    )
        pass;                   app.msg_status(str(ssnew))
        if ssnew is None:   return
        ssnew       = apx.icase(False,''
                    ,   ssnew.endswith(CDSESS_EXT)  , ssnew
                    ,   os.path.isfile(ssnew)       , ssnew
                    ,   True                        , ssnew+CDSESS_EXT
                    )
        if os.path.normpath(sscur)==os.path.normpath(ssnew): return
        app.app_proc(app.PROC_SAVE_SESSION, sscur)
        app.app_proc(app.PROC_SAVE_SESSION, ssnew)
        app.app_proc(app.PROC_SET_SESSION,  ssnew)
        app.msg_status(SAVED.format(stem=juststem(ssnew)))
        self.top_sess(ssnew)

    #################################################
    ## Private
    def top_sess(self, ssPath):
        ''' Set the session on the top of recent.
            Params:
                ssPath  Full path to session file
        '''
        ssPath  = os.path.normpath(ssPath)
        sess    = self._loadSess()
        rcnt    = sess['recent']
        if ssPath in rcnt:
            pos = rcnt.index(ssPath)
            if 0==pos:  return  # Already at top
            del rcnt[pos]
        rcnt.insert(0, ssPath)
        max_len = apx.get_opt('ui_max_history_menu', 10)
        del rcnt[max_len:]
        self._saveSess(sess)

    def _loadSess(self, existing=False):
        ''' See _saveSess for returned data format.
            Params
                existing    Delete path from recent if one doesnot exist
        '''
        sess    = json.loads(open(SESS_JSON).read())    if os.path.exists(SESS_JSON) else self.dfltSess
        rcnt    = sess['recent']
        if existing and 0<len(rcnt):
            sess['recent']  = list(filter(os.path.isfile, rcnt))
        return sess

    def _saveSess(self, sess):
        ''' sess py-format:
                {   'recent':[f1, f2, ...]      # Session fullpaths
                }
        '''
        open(SESS_JSON, 'w').write(json.dumps(sess, indent=2))

    def __init__(self):
        self.dfltSess   =   {'recent':[]}

def import_syn_sess(sssyn, sscud):
    """ Syn session ini-format
            [sess]
            gr_mode=4               Номер режима групп (1...)
                                        1 - one group
                                        2 - two horz
                                        3 - two vert
            gr_act=4                Номер активной группы (1..6)
            tab_act=0,0,1,2,0,0     Номера активных вкладок на каж группе (от 0, -1 значит нет вкладок)
            split=50                Позиция сплиттера (int в процентах), только для режимов 1*2, 2*1 и 1+2, иначе 50
            tabs=                   Число вкладок, оно только для оценки "много ли"
                Потом идут секции [f#] где # - номер вкладки от 0
            [f0]
            gr=                     Номер группы (1..6)
            fn=                     Имя файла utf8 (точку ".\" не парсить)
            top=10,20               Два числа - top line для master, slave
            caret=10,20             Два числа - каретка для master, slave
            wrap=0,0                Два bool (0/1) - wrap mode для master, slave
            prop=0,0,0,0,           4 числа через зап.
                - r/o (bool)
                - line nums visible (bool)
                - folding enabled (bool) - (NB! Было раньше disabled)
                - select mode (0..)
            color=                  Цвет таба (строка та же)
            colmark=                Col markers (строка та же)
            folded=                 2 строки через ";" - collapsed ranges для master, slave
    """
    cud_js  = {}
    cfgSyn  = configparser.ConfigParser()
    cfgSyn.read(sssyn, encoding='utf-8')
    for n_syn_tab in itertools.count():
        s_syn_tab   = f('f{}', n_syn_tab)
        if s_syn_tab not in cfgSyn: break#for n_syn_tab
        d_syn_tab   = cfgSyn[s_syn_tab]
        s_cud_tab   = f('{:03}', n_syn_tab)
        d_cud_tab   = cud_js.setdefault(s_cud_tab, {})
        d_cud_tab['file']   = d_syn_tab['fn']
        d_cud_tab['group']  = int(d_syn_tab['gr'])
       #for n_syn_tab
    cud_js['groups']    = max([t['group'] for t in cud_js.values()])
    pass;                      #LOG and log('cud_js=¶{}',pf(cud_js))
    open(sscud, 'w').write(json.dumps(cud_js, indent=2))
    return True
   #def import_syn_sess

def _checkAPI():
    if app.app_api_version()<'1.0.106':
        app.msg_status(NEED_NEWER_API)
        return False
    return True

#### Utils ####
def juststem(sspath):
    stem_ext    = os.path.basename(sspath)
    return stem_ext[:stem_ext.rindex('.')] if '.' in stem_ext else stem_ext