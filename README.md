# GeoReconViewer

示例 PySide6 应用，用于演示：左侧加载/浏览三维重建结果（.obj 占位），右侧嵌入离线地图（Leaflet），并用 QtWebChannel 建立 Python↔JS 通信。

快速开始
1. 创建并激活 Python 虚拟环境（Windows PowerShell）

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. 运行应用

```powershell
python main.py
```

说明
- `main.py` - PySide6 主程序。
- `assets/map.html` - 嵌入的本地 Leaflet 地图示例，使用 QtWebChannel 与 Python 交互。

后续
- 加入真正的 3D 渲染（OpenGL / pyqtgraph / trimesh + vispy），OBJ 加载与拾取。
- 实现 3D 点到经纬度的映射（需要重建的 georeference 元数据）。

离线地图准备
----------------
要让 `assets/map.html` 完全离线工作：

1. Leaflet 库（将其放到 `assets/leaflet/`）：
	- `assets/leaflet/leaflet.js`
	- `assets/leaflet/leaflet.css`
	- 如果需要，还把 `images/marker-icon.png` 等 Leaflet 资源放好（按原始目录结构）。

2. 地图底图（任选其一）：
	- 本地瓦片：把瓦片放在 `assets/tiles/{z}/{x}/{y}.png`，页面会优先使用本地瓦片。
	- 单张影像覆盖：把一张地理参考影像放到 `assets/map.jpg`（当前示例默认将其覆盖全球，需要你手动修改 bounds 以匹配实际经纬范围）。

如果你把上述文件都放好了，页面将无需网络即可渲染底图。
