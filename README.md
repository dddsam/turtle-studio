# 小海龟画室

给小学生上第一堂 Python 课的离线绘图应用。孩子在右侧修改代码并点击「运行」，左侧的小海龟会跟着指令走，编辑器同步高亮正在执行的那一行。

## 运行

使用带 Tkinter 的 Python 3.12，在项目根目录运行以下命令。

```powershell
py -3.12 app/studio.py
```

macOS 或 Linux 可使用 `python3 app/studio.py`。运行画室只需要 Python 标准库和随项目提供的图片。

## 课堂示例

- **小海龟修羊圈**打开时会画出三条边。把 `range(3)` 改成 `range(4)`，按 `Ctrl+Enter` 运行，看看小羊的围栏会怎样变化。
- **自由画布**适合边画边试。学生可以改步长、转角和颜色，也可以通过「文件」保存或打开自己的 `.py` 作品。

画室能执行课堂用的 Turtle 指令、变量、四则运算和嵌套的 `for ... in range(...)` 循环。可用指令和快捷示例见应用里的「指令手册」。

## 配套课件

[下载《小海龟修羊圈》PowerPoint](lessons/小海龟修羊圈.pptx)。第 1 至 9 页为约 15 分钟的试讲，第 10 至 15 页为自由创作活动。每页都有讲者备注，第 1 页备注附完整演示代码。

## 在 Windows 打包

在同一个 Python 环境中安装 PyInstaller，再在项目根目录运行以下命令。生成的独立程序位于 `dist/小海龟画室.exe`。

```powershell
py -3.12 -m pip install pyinstaller
py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name "小海龟画室" --icon "app/pictures/studio.ico" --add-data "app/pictures:pictures" app/studio.py
```

## 图片素材

小海龟与小羊插图来自 OpenMoji，依 CC BY-SA 4.0 使用。原始及改编素材说明见 [ARTWORK-LICENSE.txt](ARTWORK-LICENSE.txt)。项目已包含运行所需的图片；如需重新生成海龟各个朝向的图像，安装 Pillow 后运行 `python tools/art.py`。
