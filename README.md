# Summary 

Setup theo mô hình Multinode backup 

![](https://i.imgur.com/9Pb1Ttx.png)

Postman list API : [FILE](Benji_backup_API.postman_collection.json)

# =============================
# Setup environment CentOS 7(Or CentOS8)
# ==============================

## Chuẩn bị Node CentOS7 theo mô hình 

- CentOS7
- Install epel-release & update 
- Có network connect đến cụm Ceph 
- Thao tác bằng root user 

## I. Trên node Backup - Cài đặt các thành phần cần thiết 

Update 
```sh 
yum install epel-release -y 
yum update -y 
```

CMDlog
```sh
curl -Lso- https://raw.githubusercontent.com/nhanhoadocs/ghichep-cmdlog/master/cmdlog.sh | bash
```

Protect sync
```sh
cat << EOF >> /etc/sysctl.conf

# Protection SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.tcp_max_syn_backlog = 1024
EOF
sysctl -p 
```

Chronyd 
```sh
yum install chrony -y
timedatectl set-timezone Asia/Ho_Chi_Minh
systemctl start chronyd && systemctl enable chronyd
hwclock --systohc
timedatectl
```

Disable IPv6 
```sh 
cat << EOF >> /etc/sysctl.conf

# Disable IPv6
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF
sysctl -p
```

Firewalld & SElinux 
```sh
# Enbale firewalld 
systemctl enable --now firewalld 
firewall-cmd --zone=public --add-port=5000/tcp --permanent
firewall-cmd --zone=public --add-port=55051/tcp --permanent
firewall-cmd --zone=public --add-port=3306/tcp --permanent
firewall-cmd --reload 
# Disable SElinux 
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux
sed -i 's/SELINUX=permissive/SELINUX=disabled/g' /etc/sysconfig/selinux
```

Banner Login
```sh 
yum install figlet -y
figlet "Benji01" > /etc/ssh/banner.txt

sed -Ei 's|# Banner|Banner /etc/ssh/banner.txt|g' /etc/ssh/sshd_config
sed -Ei 's|#Banner none|Banner /etc/ssh/banner.txt|g' /etc/ssh/sshd_config
systemctl restart sshd
```

Timeout SSH/Console login
```sh 
cat << EOF >> /etc/profile

# Timeout console login
export TMOUT=300
EOF

sed -Ei 's|#ClientAliveInterval 0|ClientAliveInterval 300|g' /etc/ssh/sshd_config
systemctl restart sshd
```

Python3 
```sh 
yum install -y python3-setuptools
yum install -y python3-devel python3-pip python3-libs python3-setuptools
yum install -y git gcc make 
yum install -y python3-virtualenv
yum install -y git vim telnet net-tools 
```


## LVM

Create VG 
```sh 
vgcreate benji_vg /dev/vdb
```

Create Thin pool group 
```sh 
lvcreate -L 49G -T benji_vg/benji_lvthinpool 
```

Create lv 
> 100GB là dung lượng giả định 
```sh 
lvcreate -V100G -T benji_vg/benji_lvthinpool  -n cassystems
```

Format & mount 
```sh 
mkdir -p /backups/cassystems
mkfs.ext4 -F /dev/benji_vg/cassystems
UUID=$(blkid | grep cassystems | awk '{print $2}' | cut -d '=' -f2 | tr -d '"')
echo "UUID=${UUID} /backups/cassystems                    ext4    defaults        0 0" >> /etc/fstab 
```

Check 

![](https://i.imgur.com/7v8lYKD.png)

## Bước 1: Cài đặt Ceph client (ceph-common)
```sh 
cat << EOF > /etc/yum.repos.d/ceph.repo
[ceph]
name=Ceph packages for $basearch
baseurl=https://download.ceph.com/rpm-nautilus/el7/x86_64/
enabled=1
priority=2
gpgcheck=1
gpgkey=https://download.ceph.com/keys/release.asc

[ceph-noarch]
name=Ceph noarch packages
baseurl=https://download.ceph.com/rpm-nautilus/el7/noarch
enabled=1
priority=2
gpgcheck=1
gpgkey=https://download.ceph.com/keys/release.asc

[ceph-source]
name=Ceph source packages
baseurl=https://download.ceph.com/rpm-nautilus/el7/SRPMS
enabled=0
priority=2
gpgcheck=1
gpgkey=https://download.ceph.com/keys/release.asc
EOF

yum update -y
yum install ceph-common -y
```

Copy config file và key file vào `/etc/ceph/`

![](https://i.imgur.com/6K0Sx3X.png)

Bổ sung alias 
```sh 
cat << EOF >> /etc/profile

# Alias for ceph cluster 
alias ceph-conf='ceph-conf --cluster blk01-hn'
alias ceph='ceph --cluster blk01-hn'
alias rbd='rbd --cluster blk01-hn'
alias ceph-volume='ceph-volume --cluster blk01-hn'
EOF
```

Kiểm tra kết nối

![](https://i.imgur.com/4Tyk3Wn.png)

## Bước 2: Cài đặt Docker & Docker-compose 

> Mục đích chạy DB cho môi trường Dev (Có thể apply cho Prod)
```sh 
# Install Docker 
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io
systemctl start docker
systemctl enable docker

# Docker compose 
curl -L "https://github.com/docker/compose/releases/download/1.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
```


## Bước 3: Clone sourcecode Benji và install 
Clone và cài đặt benji 
```sh 
# Clone to /opt 
cd /opt
git clone https://git.fptcompute.com.vn/portal/cas-backup.git
cd cas-backup 

# Checkout branch 
git checkout dev

# Setup env 
virtualenv-3.6 -p /usr/bin/python3.6 venv
VENV_DIR=$(echo $(pwd)/venv)
source /opt/cas-backup/venv/bin/activate
cd /opt/cas-backup/src
python setup.py install 

# The links are necessary as Ceph's setup.py searches for these names 
ln -s /usr/bin/python3.6-config $VENV_DIR/bin/python-config
ln -s /usr/bin/python3.6m-config $VENV_DIR/bin/python3.6m-config
ln -s /usr/bin/python3.6m-x86_64-config $VENV_DIR/bin/python3.6m-x86_64-config

# Install lib for python3 
pip install -r /opt/cas-backup/src/requirements.txt 

# Install rbd & rados lib for python3 
yum install -y librados-devel librbd-devel
CEPH_VERSION=$(ceph -v | awk '{print $3}')
pip install "git+https://github.com/ceph/ceph@v$CEPH_VERSION#subdirectory=src/pybind/rados"
pip install "git+https://github.com/ceph/ceph@v$CEPH_VERSION#subdirectory=src/pybind/rbd"
pip install "git+https://git.fptcompute.com.vn/khanhct/shade.git@main#egg=shade"
```

Copy scripts lvm hỗ trợ create, update, delete storage name & tính toán overcommit node 
```sh 
cp -r /opt/cas-backup/scripts/lvmctl_* /usr/bin/
```

## Bước 4: Bổ sung config Benji 

Create log folder 
```sh 
mkdir -p /var/log/benji/
touch /var/log/benji/benji.log
```

Bổ sung benji config
```sh 
cat << EOF > /etc/benji.yaml
configurationVersion: '1'
databaseEngine: mysql+pymysql://backup_user:UK9TTK4nXlMMhnW9@172.16.0.129:3306/backup_db?charset=utf8mb4
defaultStorage: admin
logFile: /var/log/benji/benji.log
defaultPath: /backups
lvm_vg: benji_vg
lvm_lvthinpool: benji_lvthinpool
lvm_permit_overcommit: 1.3
bind_host: 0.0.0.0
bind_port: 5000
bind_grpc_port: 55051
thread_workers: 2
enable_secure_grpc_messaging: false
taskmanager_grpc_credential: /tmp
log_level: INFO
console_formatter: console-colored
telegram_token: 5703131882:AAEL21D5iRiLPrnrr4EESQqqagis-TXXtkA
telegram_group_id: '-748330672'
cas_mail_api_host: 172.16.4.252
cas_mail_api_port: 50051

ios:
  - name: file
    module: file
  - name: rbd
    module: rbd
    configuration:
      simultaneousReads: 3
      simultaneousWrites: 3
      cephConfigFile: /etc/ceph/blk01-hn.conf
      clientIdentifier: admin
      newImageFeatures:
        - RBD_FEATURE_LAYERING
        - RBD_FEATURE_EXCLUSIVE_LOCK
        - RBD_FEATURE_STRIPINGV2
        - RBD_FEATURE_OBJECT_MAP
        - RBD_FEATURE_FAST_DIFF
        - RBD_FEATURE_DEEP_FLATTEN

storages:
  - name: admin
    storageId: 1
    module: file
    configuration:
      path: /backups/admin
    node: backup03
    user_id: 1

nodes:
  - name: backup03
    host: 172.16.1.253
    port: 55051

grpc_managers:
  - service: benji.taskmanager.grpc.build.backup_pb2_grpc.add_BackupServiceServicer_to_server
    servicer: benji.taskmanager.grpc.servicers.BackupServicer
# - service: benji.taskmanager.grpc.build.user_pb2_grpc.add_UserServiceServicer_to_server
#   servicer: benji.taskmanager.grpc.servicers.UserServicer

ops_auth:
  username: tripleoadmin
  password: gaGq9LJekswxRpNFeG5C
  project_name: tripleoadmin
  endpoint: http://172.18.0.200:5000
  domain_name: opsldap
EOF
``` 


Allow firewall cho GRPC 
```sh 
firewall-cmd --zone=public --add-port=55051/tcp --permanent
firewall-cmd --reload 
```

## Bước 5: Setup Database 
```sh 
# Start containner MariaDB
cd /opt/cas-backup/
docker-compose up -d 

# Init DB 
source /opt/cas-backup/venv/bin/activate 
benji-command database-init 
```

Connect DB và kiểm tra tables 

![](https://i.imgur.com/5rP9jXf.png)


## II. Trên node API

## Bước 1 : Running test services  

MÔ hình running dịch vụ 

![](https://i.imgur.com/nDr6519.png)

- Mỗi node Backup sẽ deploy với DB riêng biệt (Deploy như từ bước 1 đến bước 5)
- Mỗi node Backup sẽ chạy taskmager như 1 agent 
- Redis, API và Celery task chỉ chạy trên node API

Run api 
```sh 
source /opt/cas-backup/venv/bin/activate 
benji-api 
```

Run Taskmanager
```sh 
source /opt/cas-backup/venv/bin/activate 
benji-tm
```

Run Celery - Schedule task 
```sh 
# Run worker
celery -A benji.celery:app worker --loglevel=INFO
# Run schedule
celery -A benji.celery:app beat --loglevel=INFO
```

Running node Benji01

![](https://i.imgur.com/gsgAgqi.gif)

## Bước 2 : Cài đặt Redis

Cài đặt Redis 

```sh
yum install epel-release -y
yum install redis -y
systemctl start redis.service
systemctl enable redis
```

Allow firewall cho Redis 
```sh 
firewall-cmd --zone=public --add-port=6379/tcp --permanent
firewall-cmd --reload 
```

# =============================
# Các task bổ sung 
# ==============================

## Cài đặt Pycharm để debug trực tiếp trên Server 

Cài đặt `x11vnc` hỗ trợ chạy pycharm qua SSH 
```shs 
sudo yum install x11vnc -y 
```

Download pycharm Community `https://www.jetbrains.com/pycharm/download/`

Giải nén 
```sh 
tar -zxvf pycharm-community-2021.1.1.tar.gz
```

Chạy Pycharm và setup environment 
```sh 
cd pycharm-community-2021.1.1/bin/
./pycharm.sh
```

![](https://i.imgur.com/RBuEoN5.gif)

## Chạy Benji_API, Benji_TM dưới dạng services  

QUản lý bằng supervisord 
```sh 
yum install supervisor -y 
```


```sh 
cat << EOF > /etc/supervisord.d/benji-tm.ini
; ==================================
;  celery worker supervisor
; ==================================

[program:benjitm]
command=/opt/cas-backup/venv/bin/benji-tm

user=root
numprocs=1
stdout_logfile=/var/log/supervisor/benji-tm.log
stderr_logfile=/var/log/supervisor/benji-tm.log
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true

; Start first
priority=99
EOF
```

```sh 
cat << EOF > /etc/supervisord.d/benji-api.ini
; ==================================
;  benji apis
; ==================================

[program:benjiapi]
command=/opt/cas-backup/venv/bin/benji-api

user=root
numprocs=1
stdout_logfile=/var/log/supervisor/benji-api.log
stderr_logfile=/var/log/supervisor/benji-api.log
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true

; Start after tm
priority=100
EOF
```

```sh
cat << EOF > /etc/supervisord.d/celery-beat.ini
; ================================
;  celery beat supervisor
; ================================

[program:celerybeat]
command=/opt/cas-backup/venv/bin/celery -A benji.celery:app beat --loglevel=INFO

user=root
numprocs=1
stdout_logfile=/var/log/supervisor/celery-beat.log
stderr_logfile=/var/log/supervisor/celery-beat.log
autostart=true
autorestart=true
startsecs=10

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true

; so it starts first
priority=999
EOF
```

```sh
cat << EOF > /etc/supervisord.d/celery-worker.ini

; ==================================
;  celery worker supervisor
; ==================================

[program:celeryworker]
command=/opt/cas-backup/venv/bin/celery -A benji.celery:app worker --loglevel=INFO

user=root
numprocs=1
stdout_logfile=/var/log/supervisor/celery-worker.log
stderr_logfile=/var/log/supervisor/celery-worker.log
autostart=true
autorestart=true
startsecs=10

; Need to wait for currently executing tasks to finish at shutdown.
; Increase this if you have very long running tasks.
stopwaitsecs = 600

; Causes supervisor to send the termination signal (SIGTERM) to the whole process group.
stopasgroup=true

; Set Celery priority higher than default (999)
priority=1000
EOF
```

Start service 
```sh 
systemctl start supervisord 
systemctl enable supervisord 
supervisorctl status
```

![](https://i.imgur.com/wvMGaGP.png)
## Test Schedule job retention 

Điều chỉnh `CeleryConfig` từ minutes thành seconds `./src/benji/config.py` (Line 260)
```sh 
CELERYBEAT_SCHEDULE = {
        'run-schedule-jobs': {
            'task': 'benji.tasks.schedule_job.run_schedule_job',
            'schedule': timedelta(hours=1)
        }
    }

CELERYBEAT_SCHEDULE = {
        'run-schedule-jobs': {
            'task': 'benji.tasks.schedule_job.run_schedule_job',
            'schedule': timedelta(seconds=10)
        }
    }
```

> Lưu ý cần edit `start_time` và `days_of_week` 

## Rebuild GRPC
```sh 
cd cd /opt/cas-backup/src/benji/taskmanager/grpc/
./cleanup.sh 
./build.sh 
```

## Reinstall benji  
```sh 
#!/bin/bash 
# Rebase benji 

source /opt/cas-backup/venv/bin/activate
pip uninstall benji -y 
rm -rf /opt/cas-backup/src/build
rm -rf /opt/cas-backup/src/benji.egg-info
rm -rf /opt/cas-backup/venv/bin/benji* 
deactivate

rm -f /usr/bin/lvmctl_* 

read -p 'Input branch to run: ' branchvar
cd /opt/cas-backup/
it reset --hard 
git checkout $branchvar
git pull 

source /opt/cas-backup/venv/bin/activate
cd /opt/cas-backup/src
python setup.py install
rm -rf /opt/cas-backup/src/build
rm -rf /opt/cas-backup/src/benji.egg-info

cd /opt/cas-backup
docker-compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
docker-compose up -d
 
docker ps -a 
sleep 10s

cp /opt/cas-backup/scripts/lvmctl_* /usr/bin/

source /opt/cas-backup/venv/bin/activate
benji-command database-init 
```

## Remove all datafile docker 
```sh 
# Stop the container(s) using the following command:
docker-compose down

# Delete all containers using the following command:
docker rm -f $(docker ps -a -q)

# Delete all volumes using the following command:
docker volume rm $(docker volume ls -q)

# Restart the containers using the following command:
docker-compose up -d
```
