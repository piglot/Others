#!/bin/bash
#This is a tool to run array commands remotely from users' VM and get the output on VM screen.
#Author:    Ming.Yao@emc.com
#Time:      11/4/2016

#set -x

my_echo()
{
    type=$1
    Message=$2
    case $type in
        "-I")
            echo -e "\e[32;40;1m$Message\e[0m"
            ;;
        "-W")
            echo -e "\e[33;40;1m$Message\e[0m"
            ;;
        "-E")
            echo -e "\e[31;40;1m$Message\e[0m"
            ;;
        *)
            exit 1
            ;;
    esac
}
    
mount_ssd()
{
    if [[ "$1" == "spa" ]]; then
        $remote_op_spa svc_mount -s -w || return 1
    elif [[ "$1" == "spb" ]]; then
        $remote_op_spb svc_mount -s -w || return 1
    fi
    return 0
}

check_boot_mode()
{
    echo "Checking boot mode..."

    spa_state=`$remote_op_spa get_boot_mode`
    if [[ "$spa_state" == "" ]];then
        my_echo -I "Can not get SPA boot mode. Abort."
        exit 1
    fi

    spb_state=`$remote_op_spb get_boot_mode`
    if [[ "$spb_state" == "" ]];then
        my_echo -I "Can not get SPB boot mode. Abort."
        exit 1
    fi
    
    if [[ "$spa_state" == "Normal Mode" && "$spb_state" == "Normal Mode" ]]; then
        array_status=0
        my_echo -I "SPA in normal mode."
        my_echo -I "SPB in normal mode."
    elif [[ "$spa_state" == "Normal Mode" && "$spb_state" == "Rescue Mode" ]]; then
        array_status=1
        my_echo -I "SPA in normal mode."
        my_echo -W "SPB in service mode. Trying to mount ssd..."
        mount_ssd spb || ( my_echo -E "SPB mount ssd failed. Abort.";exit 1 )
    elif [[ "$spa_state" == "Rescue Mode" && "$spb_state" == "Normal Mode" ]]; then
        array_status=2
        my_echo -W "SPA in service mode. Trying to mount ssd..."
        my_echo -I "SPB in normal mode."
        mount_ssd spa || ( my_echo -E "SPA mount ssd failed. Abort.";exit 1 )
    elif [[ "$spa_state" == "Rescue Mode" && "$spb_state" == "Rescue Mode" ]]; then
        array_status=3
        my_echo -W "SPA in service mode. Trying to mount ssd..."
        my_echo -W "SPB in service mode. Trying to mount ssd..."
        mount_ssd spa || ( my_echo -E "SPA mount ssd failed. Abort.";exit 1 )
        mount_ssd spb || ( my_echo -E "SPB mount ssd failed. Abort.";exit 1 )
    else
        my_echo -W "Unknown boot mode. Abort.";exit 1
    fi
    return 0
}


upload_image_to_ftp()
{
    [[ -d $ftp_image_dir ]] || ( echo "mkdir: $ftp_image_dir";sudo mkdir $ftp_image_dir || return 1 )
    [[ -f $ftp_image_dir$image_name ]] && echo "$ftp_image_dir$image_name exists." || ( sudo cp $local_image $ftp_image_dir;return 1 )
    return 0
}

download_image_to_array()
{
    if [[ $array_status == 0 ]]; then
        spa_image=$normal_mode_image
        spb_image=$normal_mode_image
    elif [[ $array_status == 1 ]]; then
        spa_image=$normal_mode_image
        spb_image=$service_mode_image
    elif [[ $array_status == 2 ]]; then
        spa_image=$service_mode_image
        spb_image=$normal_mode_image
    else
        spa_image=$service_mode_image
        spb_image=$service_mode_image
    fi

    echo "Downloading image from ftp to SPA..."
    ${remote_op_spa} "wget -q -c ftp://$ftp_site_ip/image/$image_name -O $spa_image" || ( my_echo -E "Downloading image to SPA failed. Abort."; exit 1 )
    echo "Copying image from SPA to SPB..."
    ${remote_op_spb} "scp peer:$spa_image $spb_image" || ( my_echo -E "Copy image from SPA to SPB failed. Abort."; exit 1 )
    return 0
}


prepare_image()
{
    echo "Uploading image file to FTP site..."
    upload_image_to_ftp || ( my_echo -E "Upload image to FTP site failed. Abort.";exit 1 )
    echo "Downloading image file to arrays..."
    download_image_to_array
    return 0
}

do_reimage()
{
    screen -dmS $array_name-spa $remote_op_spa "[[ -e $normal_mode_image ]] && remote_image=$normal_mode_image || remote_image=$service_mode_image;chmod +x $remote_image;$remote_image -- --reinit-dual" 
    screen -dmS $array_name-spb $remote_op_spb "[[ -e $normal_mode_image ]] && remote_image=$normal_mode_image || remote_image=$service_mode_image;chmod +x $remote_image;$remote_image -- --reinit-dual" 
    echo "Reimage begins. Using command 'screen -r $array_name-spa' or 'screen -r $array_name-spb' to see processes."
    return 0
}

#Begin
array_name=$1

ftp_site_ip="10.244.32.177"
spa_bmc_ip=`swarm $array_name --showipinfo | awk 'NR==2{print $3}'`
spb_bmc_ip=`swarm $array_name --showipinfo | awk 'NR==2{print $4}'`
spa_ip=`swarm $array_name --showipinfo | awk 'NR==2{print $5}'`
spb_ip=`swarm $array_name --showipinfo | awk 'NR==2{print $6}'`

remote_op_spa="ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $spa_ip -i /c4shares/Public/ssh/id_rsa.root"
remote_op_spb="ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $spb_ip -i /c4shares/Public/ssh/id_rsa.root"

local_image=$2
image_name=${local_image##*/}
ftp_image_dir="/srv/ftp/image/"
ftp_image=$ftp_image_dir$image_name
normal_mode_image_dir="/root/"
normal_mode_image=$normal_mode_image_dir$image_name
service_mode_image_dir="/mnt/ssdroot/"
service_mode_image=$service_mode_image_dir$image_name

check_boot_mode
prepare_image
do_reimage

exit 0
#End
