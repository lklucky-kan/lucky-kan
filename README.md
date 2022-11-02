test_controller.py参数详解:
-c 接受yaml profile，样例位于tea/test/profile/yaml_sample_for_test_controller.yml
注意：-c参数和以下参数可以共存，会合并处理
-s 服务器相关参数,键值对以逗号分隔不能有空格，参数根据case需要进行提供
ip=xx.xx.xx.xx,
os=linux,
user=root,
password=1,
bmc_ip=yy.yy.yy.yy
bmc_user=admin
bmc_password=admin

-i testcase相关参数
name=test_power_cycle  #对应testlib中的具体测试方法
full_name=tp-1:xxtest  #对应testlink中的名字， 可以不提供
script_opt=‘-c -y’ #对应的standalone中的老脚本的命令行参数，可以不提供
other_opt=...  #自定义的一些参数，key名字不定

-p pdu相关信息,只适用于test_controller.py，不需要pdu可以不提供
ip=xx.xx.xx.xx,
user=root,
password=1,

-o参数 其他的一些自定义参数，单个键值对
-o test_project=xx
-o test_plan=yy
-o runner=daisy

dev 测试特别注意：
-o runner=daisy #这个选项会在samba上面创建daisy文件夹，用作区分不同人员执行的测试
-o nodist #如果该case无须下发脚本用此参数
;
