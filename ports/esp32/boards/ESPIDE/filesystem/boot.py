# SPDX-License-Identifier: MIT
# Copyright (c) 2019-2026 Milan Spacek
# ESP IDE: https://espide.eu
# Released under MIT for this fork by the copyright holder on 2026-10-21.
# This file is executed on every boot (including wake-boot from deepsleep)
import gc
import os
import sys
import time
import utime
from micropython import alloc_emergency_exception_buf

# Emergency exception buffer for critical program errors
alloc_emergency_exception_buf(128)

def reset():
    from machine import reset
    reset()

def df():
  s = os.statvfs('//')
  return ('{0} MB'.format((s[0]*s[3])/1048576))

def free(full=False):
  gc.collect()
  F = gc.mem_free()
  A = gc.mem_alloc()
  T = F+A
  P = '{0:.2f}%'.format(F/T*100)
  if not full: return P
  else : return ('Total: {0} Free: {1} ({2})'.format(T,F,P))

gc.collect()


def terminal_color(txt,col=33):
    return "\033[" + str(col) + "m" + str(txt) + "\033[m" 

def printBar(num1,num2,col):
    #if num1/num2 < 
    print("[",end="")
    print((("\033[" + str(col) + "m#\033[m")*num1),end="")
    print(" " * num2,end="") 
    print("]  ",end="")

# Show device information in the terminal
def info():
    gc.collect()    
    bar100 = 30
    
    F = gc.mem_free()
    A = gc.mem_alloc()
    T = F+A
    P = A/T*100
    
    if P < 40:
        col = 32
    elif P < 60:
        col = 33
    else:
        col = 31
    
    b1 = T / bar100
    print("RAM used: ", end="")
    printBar(int(A / b1), bar100 - int(A / b1),col)
    print(terminal_color('{0:.1f}%'.format(P) + '   =   {0:.1f}kB of '.format(A / 1000) + '{0:.1f}kB'.format(T / 1000),col))

    s = os.statvfs('//')
    flash100 = (s[0]*s[2])/1048576
    flash = (s[0]*s[3])/1048576
    P = (flash100-flash)/flash100*100
    
    if P < 40:
        col = 32
    elif P < 60:
        col = 33
    else:
        col = 31
    
    b1 = flash100 / bar100
    print("Flash used: ", end="")
    printBar(int((flash100-flash) / b1), bar100 - int((flash100-flash) / b1),col)
    print(terminal_color('{0:.1f}%'.format(P) + '   =   {0:.3f}MB of '.format((flash100-flash)) + '{0:.3f}MB'.format(flash100),col)) 


_ERR_HINTS = {
    'SyntaxError': 'Syntax error (brackets, colons or quotes)',
    'IndentationError': 'Invalid indentation (spaces or tabs)',
    'NameError': 'Undefined variable or function',
    'TypeError': 'Invalid argument type or count',
    'ValueError': 'Invalid value format or range',
    'IndexError': 'Index out of range',
    'KeyError': 'Dictionary key not found',
    'AttributeError': 'Object has no such attribute or method',
    'ZeroDivisionError': 'Division by zero',
    'ImportError': 'Module import failed',
    'OSError': 'File or device error (I2C/SPI/filesystem)',
    'MemoryError': 'Out of RAM. Reduce memory usage.',
}

def _print_user_error(e):
    try:
        etype = e.__class__.__name__
    except Exception:
        etype = 'Error'
    try:
        msg = str(e)
    except Exception:
        msg = ''
    if msg:
        head = 'Program error (%s): %s' % (etype, msg)
    else:
        head = 'Program error (%s)' % etype
    try:
        print(terminal_color(head, 31))
    except Exception:
        print(head)
    hint = _ERR_HINTS.get(etype)
    if hint:
        try:
            print(terminal_color('Tip: ' + hint, 33))
        except Exception:
            print('Tip: ' + hint)
    if etype == 'OSError':
        try:
            if e.args and e.args[0] == 2:
                msg2 = "File not found (check 'idecode' and file paths)."
                try:
                    print(terminal_color('Tip: ' + msg2, 33))
                except Exception:
                    print('Tip: ' + msg2)
        except Exception:
            pass
    try:
        sys.print_exception(e)
    except Exception:
        pass



# ESP IDE program stop helper
def stop_code():
    try:
        on_exit()
    except:
        time.sleep_ms(0)


# ESP IDE program execution helper (reduced memory usage)
def run_code():
    G = globals()  # local reference reduces global lookups
    try:
        gc.collect()
        with open("idecode", "r") as f:
            src = f.read()   
        code = compile(src, "idecode", "exec")
        del src
        gc.collect()
        exec(code, G)
        del code
        gc.collect()
    except KeyboardInterrupt:
        print('Program stopped')
        gc.collect()
        stop_code()

    except MemoryError:
        gc.collect()
        try:
            print(terminal_color("ERROR: Out of RAM.", 31))
        except Exception:
            print("ERROR: Out of RAM.")

    except Exception as e:
        gc.collect()
        _print_user_error(e)

gc.collect()


