# Copyright (c) 2021, Xilinx®
# All rights reserved
#
# Author: Víctor Mayoral Vilches <victorma@xilinx.com>

def black(text):
    print("\033[30m", text, "\033[0m", sep="")


def red(text):
    print("\033[31m", text, "\033[0m", sep="")


def green(text):
    print("\033[32m", text, "\033[0m", sep="")


def yellow(text):
    print("\033[33m", text, "\033[0m", sep="")


def blue(text):
    print("\033[34m", text, "\033[0m", sep="")


def magenta(text):
    print("\033[35m", text, "\033[0m", sep="")


def cyan(text):
    print("\033[36m", text, "\033[0m", sep="")


def gray(text):
    print("\033[90m", text, "\033[0m", sep="")