# GitHub 仓库状态（已推送完成 ✅）

## 仓库地址

```
https://github.com/cc4n66rfmh-cloud/quant-hs300-dma-tf
```

> 注意用户名拼写：`cc4n66rfmh-cloud`（中间是 `4n66rfmh`，别漏掉 `r`）。

## 已完成的核对（2026-11-25）

通过 GitHub 官方接口确认，仓库真实可用：

- 仓库存在，且为 **Public**（老师可访问）
- 根目录 **14 项**：`.gitignore`、`README.md`、`main.py`、`rebuild_from_raw.py`、`requirements.txt`、`src/`、`data/`、`outputs/`、`teammate_files/`、两份报告素材、两份协作记录、`GitHub上传步骤.md`
- 提交记录 **12 次**
- 本地工作区干净，远程分支 `main` 已建立跟踪

## 发给组长（直接复制）

组长需在 **12 月 1 日前**把以下内容发到 <linzihao@scnu.edu.cn>：

```
收件人：linzihao@scnu.edu.cn
邮件名：周二下午--组编号-组长姓名-最终报告
正文：  本组 GitHub 仓库地址：
        https://github.com/cc4n66rfmh-cloud/quant-hs300-dma-tf
附件：  项目技术报告
```

## 如果以后要更新仓库内容

在你自己电脑的命令行里，进入项目文件夹后执行三行：

```bash
cd /d "C:\Users\HUAWEI\WorkBuddy\2026-11-24-21-28-57\quant_project"
git add .
git commit -m "说明这次改了什么"
git push
```

> 你电脑的系统 PATH 里没有 git，直接输 `git` 会报错"'git' 不是内部或外部命令"。
> 两个解决办法：
> 1. 在 GitHub 仓库文件夹的地址栏输入 `cmd` 打开命令行（推荐，不用配路径）；
> 2. 或者用完整路径调用：`"D:\work Buddy\WorkBuddy\resources\vendor\PortableGit\cmd\git.exe" push`。

## 常见问题

- **push 时提示认证失败**：浏览器弹窗登录授权即可；若要求 token，去 GitHub → Settings → Developer settings → Personal access tokens → Tokens(classic)，勾选 `repo` 权限生成，把 token 当密码用。
- **404 打不开**：先检查用户名是否拼成 `cc4n66rfmh-cloud`，再看仓库是否 Public。
- **推送后发现文件不对**：改完本地文件后执行上面的 `git add` / `commit` / `push` 三行即可。
