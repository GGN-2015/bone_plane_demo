# bone_plane_demo
Aimooe-STD-AP200 骨骼模型、平面切割动态效果展示。

## 安装

> [!WARNING] 
>
> 本示例程序只能在 win10/11 x86-64 系统使用.

建议使用 conda 隔离环境，具体环境需求如下：

```bash
conda create -n bone_plane_demo_env python=3.11 -y
conda activate bone_plane_demo_env

pip install py_ap200_simple_interface
pip install vtk
pip install numpy
```

## 使用

> [!WARNING] 
>
> 请使用 USB 连接 Aimooe AP-STD-200 设备
>
> 如果要使用 Ethernet，需要修改 ap200_interface.py 中的代码

请预先 3d 打印 BONE-1.new.stl 中的模型，并在指定位置安装旋光标志球。

启动：

```bash
conda activate bone_plane_demo_env
python vtk_show_plane.py
```
