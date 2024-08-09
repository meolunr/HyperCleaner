# HyperCleaner
自用 HyperOS 官改制作工具

适用于 HyperOS Android 14 高通骁龙 8 Gen2 / 8 Gen3 平台机型

## 特性
- 去除 Android 13+ 签名检查
- 去除强制 Data 分区加密
- 精简无用系统内置应用
- 精简 cust 分区推广应用
- 空白 Analytics 应用
- 去除安全组件
- 禁用关联启动对话框
- 去除应用包管理组件广告
- 免费使用主题
- 去除主题商店广告
- 禁用主题自动恢复
- 禁用历史通知折叠
- 去除状态栏 HD 图标
- 重定向通知渠道设置
- 去除锁屏相机和负一屏
- 去除短信广告
- 显示网络类型设置
- 去除应用信息举报按钮
- 更新系统应用为 ROM 打包时最新版本

## 系统应用更新
- 本工具可在打包 ROM 时更新系统应用为最新版本，避免用户在开机后需要进入应用商店二次更新这一步骤，同时也可以避免在 super 分区存储一份无用的老版本 apk 文件，有限地起到节省空间的作用

  如需使用此功能，需在打包 ROM 时通过 ADB 连接到设备，本工具将以设备上的系统应用为基准，更新 ROM 中的系统应用
- 本工具可单独制作系统应用更新 Magisk / KSU 模块，用户可通过安装模块更新修改过的系统应用，在保留修改效果的同时体验官方系统应用的新特性

  模块仅更新需要被修改的系统应用，无需修改的系统应用不会被打包进模块内，用户可自行进入应用商店内更新