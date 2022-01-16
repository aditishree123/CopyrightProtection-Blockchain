import traceback
import sys
from functools import lru_cache
from web3 import Web3
from web3.auto import w3
from web3.contract import Contract
from web3._utils.events import get_event_data
from web3._utils.abi import exclude_indexed_event_inputs, get_abi_input_names, get_indexed_event_inputs, normalize_event_input_types
from web3.exceptions import MismatchedABI, LogTopicError
from web3.types import ABIEvent
from eth_utils import event_abi_to_log_topic, to_hex
from hexbytes import HexBytes

import json
import re

def decode_tuple(t, target_field):
  output = dict()
  for i in range(len(t)):
    if isinstance(t[i], (bytes, bytearray)):
      output[target_field[i]['name']] = to_hex(t[i])
    elif isinstance(t[i], (tuple)):
      output[target_field[i]['name']] = decode_tuple(t[i], target_field[i]['components'])
    else:
      output[target_field[i]['name']] = t[i]
  return output
def decode_list_tuple(l, target_field):
  output = l
  for i in range(len(l)):
    output[i] = decode_tuple(l[i], target_field)
  return output

def decode_list(l):
  output = l
  for i in range(len(l)):
    if isinstance(l[i], (bytes, bytearray)):
      output[i] = to_hex(l[i])
    else:
      output[i] = l[i]
  return output

def convert_to_hex(arg, target_schema):
  """
  utility function to convert byte codes into human readable and json serializable data structures
  """
  output = dict()
  for k in arg:
    if isinstance(arg[k], (bytes, bytearray)):
      output[k] = to_hex(arg[k])
    elif isinstance(arg[k], (list)) and len(arg[k]) > 0:
      target = [a for a in target_schema if 'name' in a and a['name'] == k][0]
      if target['type'] == 'tuple[]':
        target_field = target['components']
        output[k] = decode_list_tuple(arg[k], target_field)
      else:
        output[k] = decode_list(arg[k])
    elif isinstance(arg[k], (tuple)):
      target_field = [a['components'] for a in target_schema if 'name' in a and a['name'] == k][0]
      output[k] = decode_tuple(arg[k], target_field)
    else:
      output[k] = arg[k]
  return output


def _get_contract(address, abi):
  if isinstance(abi, (str)):
    abi = json.loads(abi)

  contract = w3.eth.contract(address=Web3.toChecksumAddress(address), abi=abi)
  return (contract, abi)

def decode_tx(address, input_data, abi):
  if abi is not None:
    try:
      (contract, abi) = _get_contract(address,abi)
      func_obj, func_params = contract.decode_function_input(input_data)
      target_schema = [a['inputs'] for a in abi if 'name' in a and a['name'] == func_obj.fn_name][0]
      decoded_func_params = convert_to_hex(func_params, target_schema)
      return (func_obj.fn_name, json.dumps(decoded_func_params), json.dumps(target_schema))
    except:
      e = sys.exc_info()[0]
      return ('decode error', repr(e), None)
  else:
    return ('no matching abi', None, None)

# sample_abi = open('/home/ad105/btechProject/src/abis/Storage.json')

# output = decode_tx('0xaB5A0399b896b8Cd9292518fab63F4E8B977eb23', '0xf60886b5000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000e000000000000000000000000000000000000000000000000000000000000001400000000000000000000000000000000000000000000000000000000000000180000000000000000000000000000000000000000000000000000000000000002e516d5132474b3967674e384c63546936465151417472696e736475694d383241686a68344c466978584365667836000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002e516d54524d6f6f48437858366233367533544e664839376748566a484b6443776b38524831474568424c77676f3700000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000103833396566383631653536633236623800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004033333932333664333861363533616235613638393964636563623131323335326361363232366665666338623839663061323165363935376634353862343830', sample_abi)
# # 0x7a250d5630b4cf539739df2c5dacb4c659f2488d
# # 0xaB5A0399b896b8Cd9292518fab63F4E8B977eb23
# # 0x54D2fF96B5D1dC0A58741C2607363D0e2cED96F5
# print('function called: ', output[0])
# print('arguments: ', json.dumps(json.loads(output[1]), indent=2))

