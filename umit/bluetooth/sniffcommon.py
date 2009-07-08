'''
Created on 06-Jul-2009

@author: quekshuy
'''


MAX_SNIFF_TYPES = 16

#Frontline specific constants
FP_CLOCK_MASK = 0xFFFFFFF
FP_SLAVE_MASK = 0x02
FP_STATUS_SHIFT = 28
FP_TYPE_SHIFT = 3
FP_TYPE_MASK = 0xF
FP_ADDR_MASK = 7

FP_LEN_LLID_SHIFT = 2
FP_LEN_LLID_MASK = 3
FP_LEN_SHIFT = 5

LMP_TID_MASK = 1
LMP_OP1_SHIFT = 1