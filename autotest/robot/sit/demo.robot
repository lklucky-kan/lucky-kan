*** Settings ***
Documentation     Daisy testing robot！...
Library           test.testLib.base.Base


*** Variables ***
${Profile}        ${CURDIR}/profile #此处可以定义profile文件包含服务器登录信息
@{servers}        ip1  ip2  ip3   #this is a list var, can be used via @{servers}[1]
&{login_info}     user=root  password=abc  
${var}            %{PATH}   #%{} used the systems ENV VAR
${loop}            10

*** Test Cases ***
demo1
    Repeat Keyword    ${loop}   test  test_demo  

demo2
    Repeat Keyword    ${loop}   test  test_demo2 
   