## Script Version:
Rev: 2.0
1. Jira：auto-63 / TestLink ID: 44982
2. 验证网卡连通性的ip，改为传参的形式 （配置静态ip ip每个端口都配置不同的网段 ）,而不在再接入DHCP server 获取
3. 增加测试完成sdr sel message log收集，网卡PCIE 每次加载卸载之后speed， width收集
Rev: 1.1
1. Jira：auto-63 / TestLink ID: 44982
2. 只重复卸载加载连网网卡的驱动
3. 网口接入测试环境DHCP server 待测机台自动获取IP 
4. 目前验证的网卡驱动tg3 i40e igb e1000e mlx5-core
5. 添加对 EulerOS 操作系统支持，目前脚本支持的操作系统有redhat8/centos8/EulerOS/ubuntu/debian


脚本要求：可以手动输入加载卸载的次数，可以手动输入ping的对方服务器ip，可以手动输入ping ip 的次数
1. 记录系统下识别的端口数量  dmesg -c 清除日志
ifconfig -a |egrep -v 'lo|br|bond|vnet|vtap'|grep mtu |wc -l > all_before
dmesg -c
2.配置IP ping同一网段IP检测连通性
ping IP -c 4
3.ethtool -i ethx 获取驱动模块名
4.卸载网卡对应驱动
 rmmod  <module name>
5.加载卸载驱动脚本中加入睡眠时间
sleep 4
6.加载网卡对应驱动
modprobe <module name>
7.重复加载卸载驱动500次
8. 完成后生成日志文件 检测dmesg 有没有生成错误信息
ifconfig -a |egrep -v 'lo|br|bond|vnet|vtap'|grep mtu |wc -l > all_after
dmesg|egrep -i "error|fail|warn|wrong|bug|respond|pending" > dmesg
8.网口恢复IP地址，再次ping验证连通性
9.遍历所有网口
可以参考\\10.67.13.242\sit\系统测试\SIT\Project\Palos-H\Palos-H NIC Script && Tool


