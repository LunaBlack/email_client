# email_client
简单的SMTP邮件客户端

SMTP 客户端说明文件
==================


开发环境
-----------------

windows + python2


程序运行
-----------------

从命令行运行  
`python email_client.py`  

交互式输入用户ID、密码、服务器host、服务器端口、发送地址（以上几项可以预先在程序中设定）、
接收地址、邮件主题、正文的路径(正文是从文件读取的)  

经过测试的是@uiowa.edu邮箱向其它邮箱发送邮件  

`user_id: xxxxxxxxx`  
`password: **********`  
`server_host: xxxxxxxxx` 
`server_port: xxxxxxxxx` 
`email_from: name@server.com` 
（以上可预先设定，无需交互输入）
`email_to: name@server.com`  
`subject: test_sub`  
`the path of text: test_textfile`

如果需要测试其他邮箱，需要修改以上输入内容  
也可以在代码的MyEmailClient类的user_input函数中预先设定  


设计思路
-----------------

实现一个简单的SMTP协议的过程，包括建立连接、传送邮件、释放连接3个阶段  
主要目标为体现socket通信和SMTP协议过程

具体过程为：   
1. 用户输入必要信息，包括邮件信息和认证信息  
2. 开始SMTP协议通信，socket建立TCP连接  
3. 向SMTP服务器发送helo、ehlo、starttls、auth login等命令，标识身份、获得认证
4. 在认证过程中， starttls函数对socket进行了封装 ，实现加密传输；之后需要再次发送ehlo命令才能继续认证身份
5. 向SMTP服务器发送mail、rcpt、data等命令，协商是否发送邮件；若许可则发送邮件内容  
6. 发送quit命令，结束SMTP协议通信  

