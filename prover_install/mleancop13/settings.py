settings = {
    'mleancop-path': '.',

    # Eclipse prolog options
    # 'prolog': 'eclipse',
    # 'prolog path': '/usr/bin/eclipse',
    # 'prolog options': '-e',

    # SWI prolog options (see mleancop.sh for changes)
    'prolog': 'swi',
    'prolog-path': '/usr/bin/swipl',
    'prolog-options': ['--no-debug', '--stack-limit=340m'],

    # Sicstus prolog options
    # 'prolog': 'sicstus',
    # 'prolog path': '/usr/bin/sicstus',
    # 'prolog options: '--nologo --noinfo --goal',

    'print-proof': True,
    'save-proof': False,

    'TPTP-path': '.',

    # computational settings
    # set modal logic to D,T,S4,S5 or multimodal [d|t|s4|s5|multi]
    'logic': 's5',
    # set domain to constant, cumulative or varying [const|cumul|vary]
    'domain': 'const',
}

def validateSettings():
    if type(settings['print-proof']) is not bool:
        raise RuntimeError("Invalid print-proof setting value: expected bool, got " + type(settings['print-proof']))
    if type(settings['print-proof']) is not bool:
        raise RuntimeError("Invalid save-proof setting value: expected bool, got " + type(settings['save-proof']))
    if type(settings['prolog-options']) is not list:
        raise RuntimeError("Invalid prolog-options setting value: expected list, got " + type(settings['prolog-options']))
    if settings['logic'] not in ['d', 't', 's4', 's5', 'multi']:
        raise RuntimeError("Invalid logic setting value, expected [d|t|s4|s5|multi], got " + settings['logic'])
    if settings['domain'] not in ['const', 'cumul', 'vary']:
        raise RuntimeError("Invalid domain setting value, expected [const|cumul|vary], got " + settings['domain'])
