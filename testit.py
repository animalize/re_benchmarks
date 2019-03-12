# coding=utf-8

import re#gex as re
import time
import gc

try:
    import regex
except:
    regex = None

__all__ = ('testit',)

DEBUG = 0

TEMPLATE_ONCE = """\
{setup}
_t1 = time.perf_counter()
{stmt}
_t2 = time.perf_counter()
_t = _t2 - _t1
{teardown}
"""

TEMPLATE_LOOP = """\
_t1 = time.perf_counter()
for _ in range({loop}):
    {stmt}
_t2 = time.perf_counter()
_t = (_t2 - _t1) / {loop}
"""

def t2str(time):
    if time < 1e-6:
        time *= 10**9
        unit = 'nsec'
    elif time < 1e-3:
        time *= 10**6
        unit = 'usec'
    elif time < 1:
        time *= 10**3
        unit = 'msec'
    else:
        unit = 'sec'
    
    s = "%.2f %s" % (time, unit)
    return s

p = (r'(?s)'
     r'^(?:(.*?)\n={3,}\n)?'
     r'(.*?)\n-{3,}\n'
     r'(.+?)(?:\n-{3,}\n(.*))?$'
)
re_split = re.compile(p)
re_noassign = re.compile(r'(?m)^\w+\s*=\s*(.*)$')

def assertEqual(a, b):
    if a != b:
        print(a)
        print(b)
        raise Exception('assertEqual failed.')

def testit(stmts):
    if stmts is None:
        print('------------------')
        return

    # split stmts
    m = re_split.match(stmts)
    if not m:
        raise Exception("stmts format error.")

    tp = (m.group(i+1) for i in range(4))
    tp = (one if one is not None else '' for one in tp)
    tp = (one.strip() for one in tp)
    tp = ('pass' if (i > 0 and not one) else one for (i,one) in enumerate(tp))
    descript, setup, stmt, teardown = tp

    if descript:
        print(descript)

    # locals
    locals_d = {
        're' : re,
        'time' : time,
        'assertEqual' : assertEqual,
    }
    if regex:
        locals_d['regex'] = regex

    # once code ====================================
    src1 = TEMPLATE_ONCE.format(stmt=stmt, setup=setup, teardown=teardown)

    gcold = gc.isenabled()
    gc.disable()
    try:
        code1 = compile(src1, '<string>', 'exec')
        exec(code1, None, locals_d)
    except Exception as e:
        print('Exception:', e)
        print()
        print(src1)
        print()
        raise e
    else:
        _t_once = locals_d['_t']
        print('first attempt: ', t2str(_t_once), ', loop: ',
              sep='', end='', flush=True)
    finally:
        if gcold:
            gc.enable()

    # decide loop
    block = 1
    if _t_once == 0:
        loop = 200000
    elif _t_once < 0.000001:
        loop = int(15/_t_once)
        block = 8
    elif _t_once < 0.00001:
        loop = int(10/_t_once)
        block = 7
    elif _t_once < 0.001:
        loop = int(7/_t_once)
        block = 6
    elif _t_once < 0.01:
        loop = int(6/_t_once)
        block = 5
    elif _t_once < 0.1:
        loop = int(5/_t_once)
        block = 3
    elif _t_once < 0.5:
        loop = 1
        block = 15
    elif _t_once < 1:
        loop = 1
        block = 7
    elif _t_once < 15:
        loop = 1
        block = 4
    else:
        loop = 1
        block = 2
    print('%d x %d ' % (block, loop), end='', flush=True)

    # loop code ====================================
    if DEBUG:
        print()
        return _t_once, t2str(_t_once), 1, 1

    # remove assignment
    stmt = re_noassign.sub(r'\1', stmt)
    
    if loop == 1:
        src2 = TEMPLATE_ONCE.format(stmt=stmt, setup=setup, teardown="pass")
    else:
        src2 = TEMPLATE_LOOP.format(stmt=stmt, setup=setup, loop=loop)

    try:
        code2 = compile(src2, '<string>', 'exec')
    except Exception as e:
        print('Exception:', e)
        print()
        print(src2)
        print()
        raise e

    block_result = block * [None]
    for i in range(block):
        gcold = gc.isenabled()
        gc.disable()
        try:
            exec(code2, None, locals_d)
        except Exception as e:
            print('Exception:', e)
            print()
            print(src2)
            print()
            raise e
        else:
            block_result[i] = locals_d['_t']
        finally:
            if gcold:
                gc.enable()
        print('.', end='', flush=True)
    print()

    block_result.append(_t_once)
    result = min(block_result)
    print('best result:', t2str(result), '\n')

    return result, t2str(result), block, loop

