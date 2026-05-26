import os
import sys

if getattr(sys, 'frozen', False):
    base = sys._MEIPASS
    tcl_candidates = (
        os.path.join(base, '_tcl_data'),
        os.path.join(base, 'tcl8.6'),
    )
    tk_candidates = (
        os.path.join(base, '_tk_data'),
        os.path.join(base, 'tk8.6'),
    )

    for tcl_path in tcl_candidates:
        if os.path.isfile(os.path.join(tcl_path, 'init.tcl')):
            os.environ['TCL_LIBRARY'] = tcl_path
            break

    for tk_path in tk_candidates:
        if os.path.isfile(os.path.join(tk_path, 'tk.tcl')) or os.path.isfile(os.path.join(tk_path, 'ttk', 'ttk.tcl')):
            os.environ['TK_LIBRARY'] = tk_path
            break
