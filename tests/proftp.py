from fs.copy import copy_fs

addr = "172.21.160.35"
usr = "username"
psw = "password"
ftproot = "/data/"

try:
    ftpurl = 'ftp://' + usr + ":" + psw + "@" + addr + ftproot
    print("copy files between ftp "+ftpurl+" an local filesystems... ", end='')
    
    copy_fs(ftpurl, 'osfs://d:/tmp2/target/')
    print("OK")
except Exception as ex:
    print("FAILS") 