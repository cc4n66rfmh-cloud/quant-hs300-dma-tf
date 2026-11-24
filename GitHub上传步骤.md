# GitHub 仓库上传步骤（跟着点就行）

本地 git 仓库我已经帮你建好，3 次提交也完成了。你现在只需要做下面 4 步。

## 第 1 步：注册/登录 GitHub

打开 https://github.com ，用你自己的邮箱注册并登录（如果没有账号的话）。

## 第 2 步：新建一个空仓库

1. 点右上角 `+` → `New repository`
2. Repository name 填：`quant-hs300-dma-tf`（或你们组自己起的名字）
3. Description 填：`沪深300ETF双均线择时量化交易系统 - 财务管理课程项目`
4. 选 **Public**（公开，老师才能看到）
5. **不要**勾选 "Add a README file"、".gitignore"、"license"
   ——因为本地已经有这些文件，勾了会冲突
6. 点 `Create repository`

## 第 3 步：把本地仓库推送上去

建好后页面会显示一段命令。**在你电脑的命令行里**（不是这里），
进入项目文件夹 `quant_project`，依次执行下面三行：

```bash
git remote add origin https://github.com/你的用户名/quant-hs300-dma-tf.git
git branch -M main
git push -u origin main
```

> 把第一行里的 `你的用户名` 换成你自己的 GitHub 用户名。
> 如果弹出登录窗口，用浏览器登录 GitHub 授权即可。

推送成功后刷新仓库页面，就能看到全部文件、README 和 3 次提交记录了。

## 第 4 步：把仓库地址发给组长

组长要在 **12 月 1 日前**把这个地址发到 linzihao@scnu.edu.cn，邮件格式：

```
收件人：linzihao@scnu.edu.cn
邮件名：周二下午--组编号-组长姓名-最终报告
正文：  本组 GitHub 仓库地址：https://github.com/你的用户名/quant-hs300-dma-tf
附件：  项目技术报告
```

## 常见问题

- **push 时提示认证失败**：GitHub 现在不支持密码，要用 Personal Access Token。
  在 GitHub → Settings → Developer settings → Personal access tokens → Tokens(classic)
  生成一个新的，勾选 `repo` 权限，把 token 当密码用。
- **推送后发现文件不对**：在本地改好后执行
  `git add .` 然后 `git commit -m "说明"` 再 `git push`，就能更新。
- **不知道自己有没有 git**：我已经确认你电脑上有 git（版本 2.55）。
