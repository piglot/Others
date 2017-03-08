#!/bin/bash 

function usage()
{
echo -e "
NAME	    push.sh

Usage:      ./push.sh <options> <machinespec> ...

Note:
1. Please put the 'push' directory under path: /home/c4dev/
2. This script should only be executed on your VM. 
3. <machinespec> can be a name of an array in local lab or on swarm, it also can be an IP address of a local host.
	For example: 'br6', 'BR7', 'OB-S2006', 'BR-H1001' ,'10.62.54.107'... 

The following general options are supported:

	    --help					
		Show the usage of this shell script

	    --showip
		Show all host ip of local Bearcat machines	

	    --checkmode <[--all][machinespec1 machinespec2 machinespec3 ...]>
		Use "--all" to show boot mode of all local hosts in machine_info.txt	
		  >./push.sh --checkmode --all
		You can specify one or more given machine name to show boot mode of them
		  >./push.sh --checkmode BR-S006 BR-H1101 10.62.54.107 br10

	    --cmd <command> <[--all][machinespec1 machinespec2 machinespec3 ...]>		 
		The <command> will be executed on your specific machine and show all results together on current screen.
		And the command should be surrounded with double quotation marks.
		  >./push.sh --cmd "cat /.version" BR7 10.62.54.107 BR-H1101
		You can user "--all" instead of machine name to show cmd results of all local hosts in machine_info.txt

	    --bfupgrade <machinespec> <workspace>	
		build diskfirmwre and do upgrade
		  >./push --bfupgrade BR-S012 /c4_working/Bearcat_bugfix/

	    --upgrade <machinespec> <path_to_gpg_file>	
		do upgrade
		  >./push --upgrade BR-S012 /home/OS.tgz.bin.gpg

	    --reimage <machinespec> <image_file>	
		Do reimage when SPA SPB in Normal Mode or Service Mode
		  >sudo ./push --reimage br11 /home/OS.tgz.bin
		Caution! To reimage a local array, you need to install ftp server on your dev VM to run this script(For a high image upload speed).
		Steps to install ftp server:
		  >yast -i vsftpd
		  > /etc/init.d/vsftpd start
"
}

function check_ping()
{
	ping -c 1 -W 2 $1 >/dev/null 2>&1 && return 0 || return 1
}


function get_dev_info()
{
        ip=$1
	machinespec=$2
	cmd=`echo $@ | cut -d ' ' -f 3-`
	
        #ip_vm=$(ifconfig -a | grep inet | grep -v 127.0.0.1 | grep -v inet6 | sed 's/^.*addr://g' | sed 's/  Bcast.*//g')
        password=c4proto!

/usr/bin/expect <<-EOF
                set timeout 5
                spawn ssh root@$ip
                        expect {
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r"
                                 }
                                "Password:" { send "$password\r" }
                                "~>" {  }
				timeout { send_user "\nssh root@$ip Connect timeout!\n";exit 1 }
				eof { send_user "\nssh root@$ip Connect Error!\n";exit 1 }
			}
		send "test -f /root/info_$ip.txt && rm /root/info_$ip.txt\r"
		send "echo -e '-----------------------------------------------------' > /root/info_$ip.txt\r"
		send "echo $machinespec >> /root/info_$ip.txt\r"
		send "$cmd >> /root/info_$ip.txt\r"
                expect "~>"
		send "exit\r"
		expect eof

                spawn scp root@$ip:/root/info_$ip.txt /home/c4dev/push
                        expect {
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r";exp_continue
                                        expect "100%"
                                        send ""
                                 }
                                "Password:" {
                                        send "$password\r";exp_continue
                                        expect "100%"
                                        send ""
                                }
                                "100%" {
                                        send ""
                                }
				timeout { send_user "\nScp root@$ip:/root/info_$ip.txt /home/c4dev/push Connect timeout!\n";exit 1 }
				eof { send_user "\nScp root@$ip:/root/info_$ip.txt /home/c4dev/push Connect Error!\n";exit 1 }
                        }
                expect eof
EOF
	return 0
}

function config_MGMT()
{

	ip=$1
	ip_mgmt=$2
	password="c4proto!"

	set timeout -1

	[[ -f /home/c4dev/get_ECOM_status ]] && rm /home/c4dev/get_ECOM_status
	
	#check ECOM status && get the primary sp.
/usr/bin/expect  <<-EOF
	        set timeout 5
	        spawn ssh root@$ip
	                expect {
				"Windows Authentication" { exit 1 }
	                        "(yes/no" {
	                                send "yes\r";exp_continue
	                                expect "Password:"
	                                send "$password\r"
	                         }
	                        "Password:" { send "$password\r" }
				timeout { send_user "\nssh root@$ip Connect timeout!\n";exit 1 }
				eof { send_user "\nssh root@$ip Lost connect!\n";exit 1 }
				"~>" 
			}
	                send "crm_mon -1 | grep ECOM > /root/get_ECOM_status.txt\r"
	                send "exit\r"
	        expect eof
	
	        spawn scp root@$ip:/root/get_ECOM_status.txt /home/c4dev/get_ECOM_status
                	expect {
				eof { send_user "\nscp get_ECOM_status.txt Lost connection\n";exit 1 }
                	        "(yes/no" {
                	                send "yes\r";exp_continue
                	                expect "Password:"
                	                send "$password_vm\r";exp_continue
                	                expect "100%"
                	         }
                	        "Password:" {
                	                send "$password_vm\r";exp_continue
                	                expect "100%"
                	        }
                	        "~>" {
                	                send "";exp_continue
                	                expect "100%"
                	        }
				timeout { send_user "\nscp root@$ip:/root/get_ECOM_status.txt Connect timeout!\n";exit 1 }
                	}
	        expect eof
EOF
	[[ -f /home/c4dev/get_ECOM_status ]] || return 1
	cat /home/c4dev/get_ECOM_status | grep "Started spa"
	status1=$?
	cat /home/c4dev/get_ECOM_status | grep "Started spb"
	status2=$?
	[[ -f /home/c4dev/get_ECOM_status ]] || rm /home/c4dev/get_ECOM_status
	if [ $status1 -eq 0 ];then
	        ip_primary=$ip_spa
	        echo -e "\e[32;40;1mECOM started on is spa !\e[0m"
	elif [ $status2 -eq 0 ];then
	        ip_primary=$ip_spb
	        echo -e "\e[32;40;1mECOM started on is spb !\e[0m"
	else
	        echo -e "\e[31;40;1mECOM is not started !\e[0m"
	        return 0
	fi
	#(1)use svc_initial_config (execute command from any SP)
	#(2)Agree the eula (execute command from the SP ECOM started on)
	#(3)Change password from Password123# to Password123! (execute command from the SP ECOM started on)
	
	#get the "gateway".
	pre=${ip_mgmt%.*}
	mid="."
	final="1"
	gateway=${pre}${mid}${final}
	
/usr/bin/expect  <<-EOF
		set timeout 8
		spawn scp config_MGMT.expect root@$ip_primary:/root/
                        expect {
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r";exp_continue
                                        expect "100%"
                                 }
                                "Password:" {
                                        send "$password\r";exp_continue
                                        expect "100%"
                                }
                                "100%" { send "" }
                                timeout { send_user "scp config_MGMT.expect Connect timeout!\n";exit 1 }
                                eof { send_user "\nscp config_MGMT.expect Lost connect\n";exit 1 }
                        }
                expect eof

                spawn ssh root@$ip_primary
                        expect {
				"Windows Authentication" { exit 1 }
				"~>" {send "\r"}
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r"
                                 }
                                "Password:" { send "$password\r" }
                                timeout { send_user "\nssh root@$ip_primary Connect timeout!\n";exit 1 }
                                eof { send_user "\nssh root@$ip_primary Lost connect!\n";exit 1 }
                        }
                        send "chmod +x /root/config_MGMT.expect && { ./config_MGMT.expect $ip_primary $gateway || echo 'run config_MGMT.expect error'; } && exit\r"
EOF

	#(4)Install license (execute command from your VM, license file found under /c4shares/Public/license/)
	cd /c4shares/Public/license
	uemcli -sslPolicy accept -noHeader -u admin -p Password123! -d $ip_mgmt -upload -f license-any-host-khp.lic license
	if [ $? -eq 0 ];then
	        echo -e "\e[32;40;1mConfig MGMT successfully !\e[0m\n"
	else
	        echo -e "\e[32;40;1mTry to config MGMT failed, please check manually.\e[0m\n"
	        return 0
	fi
	
	return 0
}

function buildfirmware()
{
	workspace_path=$1
	fwlocation=$2
	disksize=$3
	
	cd $workspace_path 

	echo -e "\e[32;40;1mReady to build disk-firmware \e[0m"
	
	(       gosp3 &&
	        build_all upgrade --args upgrade="--diskfirmware --fwlocation $fwlocation --size $disksize"  && return 0
	) &
	wait
	echo -e "\e[32;40;1mBuild disk-firmware complete\e[0m"
	return 0

}

function upgrade()
{
	ip_mgmt=$1
/usr/bin/expect <<-EOF
	set timeout -1 
	spawn uemcli -d $ip_mgmt -u admin -p Password123! -upload -f $path_to_upgrade_gpg upgrade
	expect { 
		"The default selection" { send "3\r" }
		eof { exit 1}
	}
	expect "Operation completed successfully."
	send "echo -e '\e32;40;1mupload $path_to_upgrade_gpg success !\e[0m'\r"
	send "uemcli -d $ip_mgmt -u admin -p Password123! /sys/soft/upgrade create -candId CAND_1\r"
	expect "Operation completed successfully."
	send "uemcli -d $ip_mgmt -u admin -p Password123! /sys/soft/upgrade show\r" 
	expect eof
EOF
	
	return 0
}

function reimage_local()
{
        ip=$1
	ip_vm=$(sudo /sbin/ifconfig -a | grep inet | grep -v 127.0.0.1 | grep -v inet6 | sed 's/^.*addr://g' | sed 's/  Bcast.*//g')
        path_to_bin_file=$2
        bin=${path_to_bin_file##*/}
	sudo cp $path_to_bin_file /srv/ftp/ &&
	/usr/bin/expect <<-EOF
	                spawn ssh root@$ip
	                set timeout 5
	                        expect {
					"Windows Authentication" { exit 1 }
	                                "(yes/no" {
	                                        send "yes\r";exp_continue
	                                        expect "Password:"
	                                        send "$password\r"
	                                 }
	                                "Password:" { send "$password\r" }
	                                "~>"
					timeout { send_user "\nssh root@$ip Time Out!\n";exit 1}
					eof { send_user "\nssh root@$ip Error!\n";exit 1}
	                        }
				send "/sbin/get_boot_mode\r"
				expect {
					"Normal Mode" {
						send "test -d /mnt/ssdroot/  || mkdir -p /mnt/ssdroot/\r"
						expect "~>"
	                        		send "cd /mnt/ssdroot/\r"
						send "wget ftp://$ip_vm/$bin\r"
					}
					"Service Mode"{
						send "svc_mount -s -w\r"
						expect "~>"
						send "mkdir /mnt/ssdroot/;cd /mnt/ssdroot/\r"
						send "wget ftp://10.244.20.47/$bin\r"
					}
                                	"Rescue Mode"{
						send "svc_mount -s -w \r";exp_continue
						expect "~>"
						send "echo haha\r"
                                        	send "mkdir /mnt/ssdroot/\r"
						send "wget ftp://10.244.20.47/$bin\r"
					}
				}
				expect "100%"
                                send "chmod +x $bin\r"
	                        send "./$bin -- --reinit-dual\r"
	                expect eof
	
	EOF
        return 0
}

function reimage_remote()
{
        ip=$1
        ip_vm=$(ifconfig -a | grep inet | grep -v 127.0.0.1 | grep -v inet6 | sed 's/^.*addr://g' | sed 's/  Bcast.*//g')
	password="c4proto!"
	password_vm="c4dev!"
        path_to_bin_file=$2
        bin=${path_to_bin_file##*/}
	mmZusr/bin/expect <<-EOF
                set timeout -1
                spawn ssh root@$05.33.009.1.106
                        expect {
                                "Windows Authentication" { exit 1 }
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r"
                                 }
                                "Password:" { send "$password\r" }
                                "~>"
				timeout { send_user "\nssh root@$ip Time Out!\n";exit 1}
				eof { send_user "\nssh root@$ip Error!\n";exit 1}
                        }
			send "/sbin/get_boot_mode\r"
                        expect {
                                "Normal Mode" {
					send "test -d /mnt/ssdroot/  || mkdir -p /mnt/ssdroot/\r"
                                }
                                "Service Mode" {
                                        send "svc_mount -s -w\r"
                                        send "mkdir /mnt/ssdroot/\r"
				}
				"Rescue Mode" {
					send "svc_mount -s -w\r"
                                }
                        }
			send "exit\r"
		expect eof
		spawn scp $path_to_bin_file root@$ip:/mnt/ssdroot/
                        expect {
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r";exp_continue
                                        expect "100%"
                                        send ""
                                 }
                                "Password:" {
                                        send "$password\r";exp_continue
                                        expect "100%"
                                        send ""
                                }
                                "100%" {
                                        send ""
                                }
				timeout { send_user "\nscp $path_to_bin_file root@$ip:/mnt/ssdroot/ Time Out!\n";exit 1}
				eof { send_user "\nscp $path_to_bin_file root@$ip:/mnt/ssdroot/ Error!\n";exit 1}
                        }
		expect eof
                spawn ssh root@$ip
                        expect {
                                "Windows Authentication" { exit 1 }
                                "(yes/no" {
                                        send "yes\r";exp_continue
                                        expect "Password:"
                                        send "$password\r"
                                 }
                                "Password:" { send "$password\r" }
                                "~>"
                                timeout { send_user "\nssh root@$ip Time Out!\n";exit 1}
                                eof { send_user "\nssh root@$ip Error!\n";exit 1}

                        }
                        send "cd /mnt/ssdroot/;chmod +x $bin\r"
                        send "./$bin -- --reinit-dual\r"
                expect eof
	EOF
        return 0
}

get_sp_mode()
{
	/usr/bin/expect <<-EOF
	set timeout 3 
	spawn ssh -o ServerAliveInterval=10 -o ServerAliveCountMax=1 -o ConnectTimeout=3 -o User=root -T -i /c4shares/Public/ssh/id_rsa.root $1 "/sbin/get_boot_mode"
	expect { eof { exit 1 }
		 "Windows Authentication" { exit 1 }
		 "Mode" { exit 0 }
	}
	EOF
	return $?
}

function checkmode()
{
	ip=$1
	machinespec_sp=$2
	get_sp_mode $ip | grep "Normal Mode" > /dev/null && { printf "%-20s %-20s %-20s\n" $machinespec_sp $ip "Normal Mode" >> /home/c4dev/push/mode.txt;return 0; }
	get_sp_mode $ip | grep "Service Mode" > /dev/null && { printf "%-20s %-20s %-20s\n" $machinespec_sp $ip "Service Mode" >> /home/c4dev/push/mode.txt;return 0; }
	get_sp_mode $ip | grep "Rescue Mode" > /dev/null && { printf "%-20s %-20s %-20s\n" $machinespec_sp $ip "Rescue Mode" >> /home/c4dev/push/mode.txt;return 0; }
	get_sp_mode $ip | grep "Mode" > /dev/null || { printf "%-20s %-20s %-20s\n" $machinespec_sp $ip "ssh fail" >> /home/c4dev/push/mode.txt;return 1; }

}

function get_ip()
{
	argv2=`tr '[a-z]' '[A-Z]' <<<"$2"`
	cat /home/c4dev/push/machine_info.txt | grep $argv2 > /dev/null 
	if [[ $? -eq 0 ]];then
		machine_status="local"
	        ip_mgmt=$(cat /home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 3)
	        ip_spa=$(cat /home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 4)
	        ip_spb=$(cat 05.33.009.1.106/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 5)
	        machinespec=$(cat /home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 1)
05.33.009.1.1005.33.009.1.1065.33.009.1.1005.33.009.1.106	machinespec_spa=${machinespec}"-spa"
		machinespec_spb=${machinespec}"-spb"
	/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_
	else
		machine_status="remote"
	/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_/home/c4dev/push/machine_        ip_spa=`swarm $argv2 --showipinfo | awk 'NR==2{print $3}'`
	        [[ $ip_spa == "" ]] && exit 1
	        ip_spb=`swarm $argv2 --showipinfo | awk 'NR==2{print $4}'`
	        ip_mgmt=`swarm $argv2 --showipinfo | awk 'NR==2{print $2}'`
		machinespec=$argv2
		machinespec_spa=${machinespec}"-spa"
		machinespec_spb=${machinespec}"-spb"
	fi
}

#Begin here.

[[ -f /home/c4dev/push/machine_info.txt ]] || { echo -e "\e[31;40;1mPlease put 'push.sh' and 'machine_info.txt' under /home/c4dev/push/ manually.\e[0m";exit 1; }

"8["8p'8p"]"}

case $1 in
	--showip)
		cat /home/c4dev/push/machine_info.txt
		exit 0
		;;
	"--checkmode")
		echo "waiting..."
		[[ -f /home/c4dev/push/mode.txt ]] && rm /home/c4dev/push/mode.txt
		if [[ "$2" == "--all" ]];then
			while myline=$(line)
			do
				{ echo $myline | egrep -v "/-/-/-|Name" > /dev/null || continue
				machinespec=$(echo $myline | cut -d ' ' -f 1)
				ip_spa=`echo $myline | cut -d ' ' -f 4`
				ip_spb=`echo $myline | cut -d ' ' -f 5`
				{ check_ping $ip_spa
                                  if [ $? -eq 0 ];then
                                        checkmode $ip_spa $machinespec"-spa"
                                  else
                                        printf "%-20s %-20s %-20s\n" $machinespec"-spa" $ip_spa "ping fail" >> /home/c4dev/push/mode.txt
                                  fi; 
                                } &

				{ [[ "$ip_spb" != "" ]] && check_ping $ip_spb
                                if [ $? -eq 0 ];then
                                        checkmode $ip_spb $machinespec"-spb"
                                else
                                        printf "%-20s %-20s %-20s\n" $machinespec"-spb" $ip_spb "ping fail" >> /home/c4dev/push/mode.txt
                                fi; 
				} &
				wait; }  &	
			done < /home/c4dev/push/machine_info.txt 
			wait
	                printf "%s\n" "-----------------------------------------------------"
	                printf "%-20s %-20s %-20s\n" "MachineSpec" "Ip Address" "Status"
	                printf "%s\n" "-----------------------------------------------------"
	                [[ -f /home/c4dev/push/mode.txt ]] && cat /home/c4dev/push/mode.txt | grep -v -E 'MachineSpec|---' | sort && rm /home/c4dev/push/mode.txt
	                printf "%s\n" "-----------------------------------------------------"
			exit 0
		else
			until [ -z $2 ]
			do
				{ argv2=`tr '[a-z]' '[A-Z]' <<<"$2"`
				grep $argv2 < /home/c4dev/push/machine_info.txt > /dev/null
				if [[ $? -eq 0 ]];then
				        ip_spa=$(cat /home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 4)
				        ip_spb=$(cat /home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 5)
				        machinespec=$(cat /home/c4dev/push/machine_info.txt | grep $argv2 | cut -f 1)
				
				else
				        ip_spa=`swarm $argv2 --showipinfo | awk 'NR==2{print $3}'`
				        [[ $ip_spa == "" ]] && exit 1
				        ip_spb=`swarm $argv2 --showipinfo | awk 'NR==2{print $4}'`
				        machinespec=$argv2
				fi

				{ check_ping $ip_spa
				if [ $? -eq 0 ];then
					checkmode $ip_spa $machinespec_spa"-spa"
				else
					printf "%-20s %-20s %-20s\n" $machinespec"-spa" $ip_spa "ping fail" >> /home/c4dev/push/mode.txt
				fi; } &

				{ check_ping $ip_spb
				if [ $? -eq 0 ];then
					checkmode $ip_spb $machinespec"-spb"
				else
					printf "%-20s %-20s %-20s\n" $machinespec"-spb" $ip_spb "ping fail" >> /home/c4dev/push/mode.txt
				fi; } &
				wait; }  &
			shift
			done
		fi
		wait
		printf "%s\n" "-----------------------------------------------------"
		printf "%-20s %-20s %-20s\n" "MachineSpec" "Ip Address" "Status"
		printf "%s\n" "-----------------------------------------------------"
		[[ -f /home/c4dev/push/mode.txt ]] && cat /home/c4dev/push/mode.txt | grep -v -E 'MachineSpec|---' | sort && rm /home/c4dev/push/mode.txt
		printf "%s\n" "-----------------------------------------------------"
		exit 0
		;;
	"--cmd")
		echo "waiting..."
                [[ -f /home/c4dev/push/info.txt ]] && rm /home/c4dev/push/info.txt
		cmd=$2
                if [[ "$3" == "--all" ]];then
                        while myline=$(line)
                        do
                                { echo $myline | egrep -v "/-/-/-|Name" > /dev/null || continue
                                machinespec=$(echo $myline | cut -d ' ' -f 1)
                                machinespec_spa=$machinespec"-spa"
                                machinespec_spb=$machinespec"-spb"
                                ip_spa=`echo $myline | cut -d ' ' -f 4`
                                ip_spb=`echo $myline | cut -d ' ' -f 5`

                                { check_ping $ip_spa
                                if [ $? -eq 0 ];then
                                        get_dev_info $ip_spa $machinespec_spa $cmd
                                        [ -f /home/c4dev/push/info_$ip_spa.txt ] && cat /home/c4dev/push/info_$ip_spa.txt >> /home/c4dev/push/info.txt && rm /home/c4dev/push/info_$ip_spa.txt
                                else
                                        printf "%-20s %-20s %-20s\n" $machinespec_spa $ip_spa "ping fail" >> /home/c4dev/push/info.txt
                                fi; } &

                                { check_ping $ip_spb
                                if [ $? -eq 0 ];then
                                        get_dev_info $ip_spb $machinespec_spb $cmd
                                        [ -f /home/c4dev/push/info_$ip_spb.txt ] && cat /home/c4dev/push/info_$ip_spb.txt >> /home/c4dev/push/info.txt && rm /home/c4dev/push/info_$ip_spb.txt
                                else
                                        printf "%-20s %-20s %-20s\n" $machinespec_spb $ip_spb "ping fail" >> /home/c4dev/push/info.txt
                                fi; } &
                                wait; } > /dev/null &
			done < /home/c4dev/push/machine_info.txt 
		else 
                	until [ -z $3 ]
                	do
				{ argv3=`tr '[a-z]' '[A-Z]' <<<"$3"`
			        grep $argv3 < /home/c4dev/push/machine_info.txt > /dev/null
                		if [[ $? -ne 0 ]];then
                		        ip_spa=`swarm $argv3 --showipinfo | awk 'NR==2{print $3}'`
                		        [[ $ip_spa == "" ]] && exit 1
                		        ip_spb=`swarm $argv3 --showipinfo | awk 'NR==2{print $4}'`
                		        ip_mgmt=`swarm $argv3 --showipinfo | awk 'NR==2{print $2}'`
                		        machinespec=$argv3
                		else
                		        argv3=`tr '[a-z]' '[A-Z]' <<<"$3"`
                		        cat /home/c4dev/push/machine_info.txt | grep $argv3 > /dev/null || { echo "can't find $2.";exit 1; }
                		        ip_mgmt=$(cat /home/c4dev/push/machine_info.txt | grep $argv3 | cut -f 3)
                		        ip_spa=$(cat /home/c4dev/push/machine_info.txt | grep $argv3 | cut -f 4)
                		        ip_spb=$(cat /home/c4dev/push/machine_info.txt | grep $argv3 | cut -f 5)
                		        machinespec=$(cat /home/c4dev/push/machine_info.txt | grep $argv3 | cut -f 1)
                		fi
                	        machinespec_spa=${machinespec}"-spa"
                	        machinespec_spb=${machinespec}"-spb"

                	        { check_ping $ip_spa
                	        if [ $? -eq 0 ];then
                	                get_dev_info $ip_spa $machinespec_spa $cmd
					[ -f /home/c4dev/push/info_$ip_spa.txt ] && cat /home/c4dev/push/info_$ip_spa.txt >> /home/c4dev/push/info.txt && rm /home/c4dev/push/info_$ip_spa.txt
                	        else
                	                printf "%-20s %-20s %-20s\n" $machinespec_spa $ip_spa "ping fail" >> /home/c4dev/push/info.txt
					[ -f /home/c4dev/push/info_$ip_spa.txt ] && cat /home/c4dev/push/info_$ip_spa.txt >> /home/c4dev/push/info.txt && rm /home/c4dev/push/info_$ip_spa.txt
                	        fi; } &

                	        { check_ping $ip_spb
                	        if [ $? -eq 0 ];then
                	                get_dev_info $ip_spb $machinespec_spb $cmd
					[ -f /home/c4dev/push/info_$ip_spb.txt ] && cat /home/c4dev/push/info_$ip_spb.txt >> /home/c4dev/push/info.txt && rm /home/c4dev/push/info_$ip_spb.txt
                	        else
                	                printf "%-20s %-20s %-20s\n" $machinespec_spb $ip_spb "ping fail" >> /home/c4dev/push/info.txt
                	        fi; } &
                	        wait; } > /dev/null &
                	        shift
			done
		fi
		wait
                [[ -f /home/c4dev/push/info.txt ]] && cat /home/c4dev/push/info.txt && rm /home/c4dev/push/info.txt
                printf "%s\n" "-----------------------------------------------------"
                exit 0
		;;
	"--checkMGMT")
		[ $# -ne 2 ] && usage && exit 1
        	check_ping $ip_mgmt && { echo -e "\e[32;40;1mPing MGMT($ip_mgmt) success.\e[0m";exit 0; } || echo -e "\e[31;40;1mPing MGMT($ip_mgmt) failed.\e[0m"
		check_ping $ip_spa && check_ping $ip_spb &&
#              	checkmode $ip_spa && checkmode $ip_spb &&
		config_MGMT $ip_spa $ip_mgmt || config_MGMT $ip_spb $ip_mgmt
		exit 0
		;;
	"--bfupgrade")
	        workspace_path=$3
		parent_path=`cd $workspace_path;cd ..;pwd`
		[ "$parent_path" != "/c4_working" ] && echo -e "\n\t\e[31;43;1mError! The 3th parameter is path to your workspace.\e[0m" && exit 1
		[ $# -ne 3 ] && usage && exit 1
		#build image
		fwlocation="/home/c4dev/push/firmware/"
		disksize="600GB"
		buildfirmware $workspace_path $fwlocation $disksize &&
		
		#check MGMT
		check_ping $ip_mgmt || echo -e "\e[31;40;1mMGMT can not access !\e[0m\n" && exit 1
		#configui $ip_spa $ip_spb $ip_mgmt

		#check spa spb
		checkmode $ip_spa || exit 1
		checkmode $ip_spb || exit 1

		#upgrade
		path=`cd $workspace_path;cd output/upgrade/GNOSIS_DEBUG/;pwd`
		link="/"
		gpg_file=`cd $workspace_path;cd output/upgrade/GNOSIS_DEBUG/;ls *.gpg`
		link="/"
		path_to_gpg_file=${path}${link}${gpg_file}
		#upgrade $ip_mgmt $path_to_gpg_file  &
		wait
		exit 0;;
	"--upgrade")
                #check MGMT
                check_ping $ip_mgmt
		if [ $? -ne 0 ];then
			echo -e "\e[31;40;1mCan not access MGMT. Please check it manully.\e[0m" && exit 1
		fi
                #configui $ip_spa $ip_spb $ip_mgmt

                path_to_gpg_file=$3
                upgrade $ip_mgmt $path_to_gpg_file 
                #wait
                exit 0;;
	"--reimage")
		[ $# -ne 3 ] && usage && exit 1
		[[ $3 != *.tgz.bin ]] && echo -e "\n\t\e[31;43;1mError!  Image file name is invalid.\e[0m" && usage && exit 1
		path_to_bin_file=$3
		[[ "$machine_status" == "local" ]] && reimage_local $ip_spa $path_to_bin_file &
		[[ "$machine_status" == "local" ]] && reimage_local $ip_spb $path_to_bin_file &
		[[ "$machine_status" == "remote" ]] && reimage_remote $ip_spa $path_to_bin_file & 
		[[ "$machine_status" == "remote" ]] && reimage_remote $ip_spb $path_to_bin_file &
		wait
		exit 0;;
	"--help")
		usage
		exit 0;;
        *)
                usage
                exit 1;;
esac
