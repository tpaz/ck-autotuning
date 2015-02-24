#
# Collective Knowledge (platform detection)
#
# See CK LICENSE.txt for licensing details
# See CK Copyright.txt for copyright details
#
# Developer: Grigori Fursin, Grigori.Fursin@cTuning.org, http://cTuning.org/lab/people/gfursin
#

cfg={}  # Will be updated by CK (meta description of this module)
work={} # Will be updated by CK (temporal data)
ck=None # Will be updated by CK (initialized CK kernel) 

# Local settings

##############################################################################
# Initialize module

def init(i):
    """

    Input:  {}

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0
            }

    """
    return {'return':0}

##############################################################################
# collect info about platforms

def analyze(i):
    """
    Input:  {
              (os)        - OS module to check (if omitted, analyze host)
              (device_id) - device id if remote and adb
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              os_ck
              os
            }

    """

    import os

    o=i.get('out','')

    host={}
    target={}
    work={}

    xos=i.get('os','')

    # Get a few host parameters + target platform
    r=ck.get_platform({'os_uoa':xos, 'find_close':'yes'})
    if r['return']>0: return r

    host_name=r['platform']
    host_bits=r['bits']
    host_cfg=ck.cfg.get('shell',{}).get(host_name,{})

    host['name']=host_name
    host['bits']=host_bits
    host['cfg']=host_cfg

    ro=host_cfg.get('redirect_stdout','')

    # Retrieved (most close) platform
    os_uoa=r['os_uoa']
    os_uid=r['os_uid']

    os_dict=r['os_dict']

    target['uoa']=os_uoa
    target['uid']=os_uid
    target['dict']=os_dict

    target_system_name=''
    target_system_model=''
    target_os_name_short=''
    target_os_name_long=''
    target_cpu=''
    target_freq=''
    target_freq_max=''

    device_id=i.get('device_id','')

    # Checking platform
    os_bits=os_dict.get('bits','')
    os_win=os_dict.get('windows_base','')

    remote=os_dict.get('remote','')
    if remote=='yes':
       remote_init=os_dict.get('remote_init','')
       if remote_init!='':
          if o=='con':
             ck.out('Initializing remote device:')
             ck.out('  '+remote_init)
             ck.out('')

          rx=os.system(remote_init)
          if rx!=0:
             if o=='con':
                ck.out('')
                ck.out('Non-zero return code :'+str(rx)+' - likely failed')
             return {'return':1, 'error':'remote device initialization failed'}

       # Get devices
       rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
       if rx['return']>0: return rx
       fn=rx['file_name']

       adb_devices=os_dict.get('adb_devices','')
       adb_devices=adb_devices.replace('$#redirect_stdout#$', ro)
       adb_devices=adb_devices.replace('$#output_file#$', fn)

       if o=='con':
          ck.out('')
          ck.out('Receiving list of devices:')
          ck.out('  '+adb_devices)

       rx=os.system(adb_devices)
       if rx!=0:
          if o=='con':
             ck.out('')
             ck.out('Non-zero return code :'+str(rx)+' - likely failed')
          return {'return':1, 'error':'access to remote device failed'}

       # Read and parse file
       rx=ck.load_text_file({'text_file':fn})
       if rx['return']>0: return rx
       s=rx['string']

       devices=[]
       q=0
       while (q>=0):
          q1=s.find('\n',q)
          if q1>=0:
             s1=s[q:q1]

             if q!=0: #ignore first line in ADB
                q2=s1.find('\t')
                if q2>0:
                   s2=s1[0:q2]
                   devices.append(s2)

             q=q1+1
          else:
             q=-1

       target['devices']=devices

       if os.path.isfile(fn): os.remove(fn)

       if o=='con':
          ck.out('')
          ck.out('Available remote devices:')
          for q in devices:
              ck.out('  '+q)
          ck.out('')

       if device_id!='':
          if device_id not in devices:
             return {'return':1, 'error':'Device ID was not found in the list of attached devices'}
       else:
          if len(devices)>0:
             device_id=devices[0]

       # Get all params
       params={}

       rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
       if rx['return']>0: return rx
       fn=rx['file_name']

       adb_params=os_dict.get('adb_all_params','')
       adb_params=adb_params.replace('$#redirect_stdout#$', ro)
       adb_params=adb_params.replace('$#output_file#$', fn)

       if o=='con':
          ck.out('')
          ck.out('Receiving all parameters:')
          ck.out('  '+adb_params)

       rx=os.system(adb_params)
       if rx!=0:
          if o=='con':
             ck.out('')
             ck.out('Non-zero return code :'+str(rx)+' - likely failed')
          return {'return':1, 'error':'access to remote device failed'}

       # Read and parse file
       rx=ck.load_text_file({'text_file':fn})
       if rx['return']>0: return rx
       s=rx['string']

       devices=[]
       q=0
       while (q>=0):
          q1=s.find('\n',q)
          if q1>=0:
             s1=s[q:q1].strip()

             q2=s1.find(']: [')
             k=''
             if q2>=0:
                k=s1[1:q2].strip()
                v=s1[q2+4:].strip()
                v=v[:-1].strip()
 
                params[k]=v

             q=q1+1
          else:
             q=-1

       target['params']=params

       if os.path.isfile(fn): os.remove(fn)

       # Get params
       x1=params.get('ro.product.brand','')
       x2=params.get('ro.product.board','')

       target_system_name=x1+' '+x2

       target_system_model=params.get('ro.build.id','')

       target_os_name_long=params.get('ro.build.kernel.version','')
       target_os_name_short='Android '+params.get('ro.build.version.release','')
       





    else:
       try:
          from cpuinfo import cpuinfo
       except Exception as e:
          if o=='con':
             ck.out('You need to install py-cpuinfo module:')
             if os_win=='win':
                ck.out('     sudo apt-get install python-pip')
                ck.out('     sudo pip install py-cpuinfo')
             else:
                ck.out('     sudo apt-get install python-pip')
                ck.out('     sudo pip install py-cpuinfo')
             ck.out('')

             return {'return':1, 'error':'python cpuinfo module is not installed - install it using "pip install py-cpuinfo"'}

       info=cpuinfo.get_cpu_info()

       target['system_info']=info

       target_cpu=info.get('brand','')

       import platform
       target_os_name_long=platform.platform()
       target_os_name_short=platform.system()+' '+platform.release()

       if os_win=='yes':
          r=get_from_wmic({'cmd':'cpu get CurrentClockSpeed'})
          if r['return']>0: return r
          target_freq=r['value']

          r=get_from_wmic({'cmd':'cpu get MaxClockSpeed'})
          if r['return']>0: return r
          target_freq_max=r['value']

          r=get_from_wmic({'cmd':'csproduct get vendor'})
          if r['return']>0: return r
          x1=r['value']

          r=get_from_wmic({'cmd':'csproduct get version'})
          if r['return']>0: return r
          x2=r['value']

          target_system_name=x1+' '+x2

          r=get_from_wmic({'cmd':'computersystem get model'})
          if r['return']>0: return r

          target_system_model=r['value']
       else:
          q1=target_os_name_short.find('-')
          if q1>=0:
             target_os_name_short=target_os_name_short[0:q1]

          x1=''
          x2=''

          file_with_vendor='/sys/devices/virtual/dmi/id/sys_vendor'
          if os.path.isfile(file_with_vendor):
             r=ck.load_text_file({'text_file':file_with_vendor})
             if r['return']>0: return r
             x1=r['string'].strip()

          file_with_version='/sys/devices/virtual/dmi/id/product_version'
          if os.path.isfile(file_with_version):
             r=ck.load_text_file({'text_file':file_with_version})
             if r['return']>0: return r
             x2=r['string'].strip()

          if x1!='' and x2!='':
             target_system_name=x1+' '+x2


#xyz
          file_with_model='/sys/devices/virtual/dmi/id/product_name'
          if os.path.isfile(file_with_model):
             r=ck.load_text_file({'text_file':file_with_model})
             if r['return']>0: return r
             target_system_model=r['string'].strip()

          if target_system_name=='' or target_system_model=='':
             return {'return':1, 'error':'can\'t get system vendor/model in module "platform" with action "analyze" - please, help improve it for your system'}



    target['target_os_name_long']=target_os_name_long
    target['target_os_name_short']=target_os_name_short
    target['target_os_bits']=os_bits
    target['target_system_name']=target_system_name
    target['target_system_model']=target_system_model
    target['cpu_name']=target_cpu
    target['cpu_freq']=target_freq
    target['cpu_freq_max']=target_freq_max

    if o=='con':
       ck.out('Target CK OS UOA:   '+os_uoa+' ('+os_uid+')')
       ck.out('')
       ck.out('Long OS name:       '+target_os_name_long)
       ck.out('Short OS name:      '+target_os_name_short)
       ck.out('Target bits:        '+os_bits)
       ck.out('')
       ck.out('System name:        '+target_system_name)
       ck.out('System model:       '+target_system_model)
       ck.out('')
       ck.out('CPU name:           '+target_cpu)
       ck.out('')
       ck.out('CPU frequency:      '+target_freq)
       ck.out('CPU max frequency:  '+target_freq_max)

    return {'return':0, 'host':host, 'target':target, 'device_id':device_id}

##############################################################################
# collect data using wmic on Windows

def get_from_wmic(i):
    """
    Input:  {
              cmd - cmd for wmic
            }

    Output: {
              return       - return code =  0, if successful
                                         >  0, if error
              (error)      - error text if return > 0

              value        - obtained value
            }

    """

    value=''

    import os

    rx=ck.gen_tmp_file({'prefix':'tmp-ck-'})
    if rx['return']>0: return rx
    fn=rx['file_name']

    cmd='wmic '+i.get('cmd','')+' > '+fn
    r=os.system(cmd)
    if r!=0:
       return {'return':1, 'error':'command returned non-zero value: '+cmd}

    # Read and parse file
    rx=ck.load_text_file({'text_file':fn, 'encoding':'utf16'})
    if rx['return']>0: return rx
    s=rx['string']

    devices=[]
    q=0
    while (q>=0):
       q1=s.find('\n',q)
       if q1>=0:
          s1=s[q:q1]

          if q!=0: #ignore first line in ADB
             q2=s1.find('\n',q1+1)
             if q2>=0:
                s1=s1[0:q2]
             value=s1.strip()
             q=-1

          q=q1+1
       else:
          q=-1

    if os.path.isfile(fn): os.remove(fn)

    return {'return':0, 'value':value}